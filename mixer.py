import numpy as np
import sounddevice as sd
import collections
import threading

class Mixer:
    """
    Saída principal (VB-Cable): mic + clipes
    Monitor local (alto-falantes): apenas clipes (sem mic) para evitar eco.
    """
    def __init__(self, samplerate=48000, channels=2, blocksize=256):
        self.sr = samplerate
        self.ch = channels
        self.blocksize = blocksize

        self.in_dev = None
        self.out_dev = None
        self.mon_dev = None

        self._in_stream = None
        self._out_stream = None
        self._mon_stream = None

        self._lock = threading.Lock()
        # cada clipe mantém dois cursores: principal e monitor
        self._clips = []  # {"data": np.ndarray [N,2], "pos_main":int, "pos_mon":int}
        self._mic_queue = collections.deque()
        self._mic_queue_frames = 0

        self.gain = 1.0       # ganho clipes (principal)
        self.mic_gain = 1.0   # ganho mic   (principal)
        self.monitor_gain = 1.0  # ganho clipes no monitor

    def _get_device_sr(self, dev_idx):
        try:
            d = sd.query_devices(dev_idx)
            sr = int(d.get("default_samplerate") or self.sr)
            return max(8000, min(192000, sr))
        except Exception:
            return self.sr

    def set_devices(self, in_dev_idx, out_dev_idx, mon_dev_idx=None):
        """Define mic, saída principal e (opcional) monitor."""
        restart_in  = (in_dev_idx != self.in_dev)
        restart_out = (out_dev_idx != self.out_dev)
        restart_mon = (mon_dev_idx != self.mon_dev)

        self.in_dev = in_dev_idx
        self.out_dev = out_dev_idx
        self.mon_dev = mon_dev_idx

        if restart_out and self.out_dev is not None:
            self.sr = self._get_device_sr(self.out_dev)

        if restart_in:
            self._stop_input()
            if self.in_dev is not None:
                self._start_input()

        if restart_out:
            self._stop_output()
            if self.out_dev is not None:
                self._start_output()

        if restart_mon:
            self._stop_monitor()
            if self.mon_dev is not None:
                self._start_monitor()

    def set_monitor_device(self, mon_dev_idx):
        """Ativa/desativa o monitor local sem alterar mic/saída principal."""
        if mon_dev_idx == self.mon_dev:
            return
        self.mon_dev = mon_dev_idx
        self._stop_monitor()
        if self.mon_dev is not None:
            self._start_monitor()

    # ----- Input (mic) -----
    def _start_input(self):
        ch_in = 1
        try:
            dinfo = sd.query_devices(self.in_dev)
            ch_in = 2 if dinfo["max_input_channels"] >= 2 else 1
        except Exception:
            ch_in = 1

        def in_cb(indata, frames, time_info, status):
            if status: pass
            if indata is None: return
            mic = indata.astype(np.float32, copy=False)
            if mic.shape[1] == 1:
                mic = np.repeat(mic, 2, axis=1)
            elif mic.shape[1] > 2:
                mic = mic[:, :2]
            with self._lock:
                self._mic_queue.append(mic.copy())
                self._mic_queue_frames += mic.shape[0]
                max_frames = self.blocksize * 5
                while self._mic_queue_frames > max_frames and len(self._mic_queue) > 1:
                    old = self._mic_queue.popleft()
                    self._mic_queue_frames -= old.shape[0]

        self._in_stream = sd.InputStream(
            device=self.in_dev,
            samplerate=self.sr,
            blocksize=self.blocksize,
            dtype='float32',
            channels=ch_in,
            latency='low',
            callback=in_cb
        )
        self._in_stream.start()

    def _stop_input(self):
        try:
            if self._in_stream is not None:
                self._in_stream.stop(); self._in_stream.close()
        finally:
            self._in_stream = None
            with self._lock:
                self._mic_queue.clear()
                self._mic_queue_frames = 0

    # ----- Output principal (mix mic + clipes) -----
    def _start_output(self):
        def out_cb(outdata, frames, time_info, status):
            if status: pass
            mix = np.zeros((frames, self.ch), dtype=np.float32)

            with self._lock:
                # mic
                need = frames
                chunks = []
                while need > 0 and self._mic_queue:
                    blk = self._mic_queue[0]
                    if blk.shape[0] <= need:
                        chunks.append(blk)
                        self._mic_queue.popleft()
                        self._mic_queue_frames -= blk.shape[0]
                        need -= blk.shape[0]
                    else:
                        chunks.append(blk[:need])
                        self._mic_queue[0] = blk[need:]
                        self._mic_queue_frames -= need
                        need = 0
                if chunks:
                    mic = np.vstack(chunks)
                    if mic.shape[0] < frames:
                        pad = np.zeros((frames - mic.shape[0], 2), dtype=np.float32)
                        mic = np.vstack([mic, pad])
                    mix += mic * self.mic_gain

                # clipes (cursor principal)
                to_remove = []
                for i, clip in enumerate(self._clips):
                    data = clip["data"]; pos = clip["pos_main"]
                    end = min(pos + frames, data.shape[0])
                    chunk = data[pos:end]
                    if chunk.shape[0] < frames:
                        pad = np.zeros((frames - chunk.shape[0], data.shape[1]), dtype=data.dtype)
                        chunk = np.vstack([chunk, pad])
                    mix += chunk * self.gain
                    clip["pos_main"] = end
                    # remoção só quando AMBOS terminaram (principal e monitor)
                    if clip["pos_main"] >= data.shape[0] and clip["pos_mon"] >= data.shape[0]:
                        to_remove.append(i)
                for idx in reversed(to_remove):
                    self._clips.pop(idx)

            np.clip(mix, -1.0, 1.0, out=mix)
            outdata[:] = mix

        self._out_stream = sd.OutputStream(
            device=self.out_dev,
            samplerate=self.sr,
            blocksize=self.blocksize,
            dtype='float32',
            channels=self.ch,
            latency='low',
            callback=out_cb
        )
        self._out_stream.start()

    def _stop_output(self):
        try:
            if self._out_stream is not None:
                self._out_stream.stop(); self._out_stream.close()
        finally:
            self._out_stream = None

    # ----- Monitor local (somente clipes) -----
    def _start_monitor(self):
        def mon_cb(outdata, frames, time_info, status):
            if status: pass
            mix = np.zeros((frames, self.ch), dtype=np.float32)
            with self._lock:
                for clip in self._clips:
                    data = clip["data"]; pos = clip["pos_mon"]
                    end = min(pos + frames, data.shape[0])
                    chunk = data[pos:end]
                    if chunk.shape[0] < frames:
                        pad = np.zeros((frames - chunk.shape[0], data.shape[1]), dtype=data.dtype)
                        chunk = np.vstack([chunk, pad])
                    mix += chunk * self.monitor_gain
                    clip["pos_mon"] = end
                # remoção ocorre no callback principal quando ambos terminam
            np.clip(mix, -1.0, 1.0, out=mix)
            outdata[:] = mix

        self._mon_stream = sd.OutputStream(
            device=self.mon_dev,
            samplerate=self.sr,
            blocksize=self.blocksize,
            dtype='float32',
            channels=self.ch,
            latency='low',
            callback=mon_cb
        )
        self._mon_stream.start()

    def _stop_monitor(self):
        try:
            if self._mon_stream is not None:
                self._mon_stream.stop(); self._mon_stream.close()
        finally:
            self._mon_stream = None

    # ----- Controle -----
    def play_clip(self, data, sr):
        if sr != self.sr:
            raise RuntimeError(f"SR diferente ({sr} vs {self.sr}). Ajuste o cache para {self.sr}.")
        if data.ndim == 1:
            data = np.stack([data, data], axis=1)
        elif data.shape[1] == 1:
            data = np.repeat(data, 2, axis=1)
        elif data.shape[1] > 2:
            data = data[:, :2]
        with self._lock:
            self._clips.append({"data": data.astype(np.float32, copy=False), "pos_main": 0, "pos_mon": 0})

    def stop_all(self):
        with self._lock:
            self._clips.clear()

    def stop(self):
        self._stop_input()
        self._stop_output()
        self._stop_monitor()
