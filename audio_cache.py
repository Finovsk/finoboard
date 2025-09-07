import os, threading, shutil, subprocess
import numpy as np
from pydub import AudioSegment
from json import JSONDecodeError

class AudioCache:
    def __init__(self, target_samplerate=48000, target_channels=2):
        self.sr = target_samplerate
        self.ch = target_channels
        self.cache = {}
        self.lock = threading.Lock()

    def set_target(self, samplerate:int, channels:int=2):
        with self.lock:
            if self.sr != samplerate or self.ch != channels:
                self.sr = samplerate
                self.ch = channels
                self.cache.clear()

    def _ffmpeg_paths(self):
        ffm = getattr(AudioSegment, "converter", None) or shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        ffp = getattr(AudioSegment, "ffprobe", None) or shutil.which("ffprobe") or shutil.which("ffprobe.exe")
        return ffm, ffp

    def load(self, path):
        mtime = os.path.getmtime(path)
        key = (path, mtime, self.sr, self.ch)
        with self.lock:
            if key in self.cache:
                return self.cache[key]

        try:
            # caminho normal (usa ffprobe para metadados)
            seg = AudioSegment.from_file(path).set_frame_rate(self.sr).set_channels(self.ch).set_sample_width(2)
        except JSONDecodeError as jde:
            # saída do ffprobe não era JSON -> explicar melhor
            ffm, ffp = self._ffmpeg_paths()
            hint = []
            if not ffp:
                hint.append("ffprobe não encontrado no PATH.")
            if not ffm:
                hint.append("ffmpeg não encontrado no PATH.")
            raise RuntimeError(
                "Falha ao analisar o arquivo de áudio (ffprobe retornou saída inválida). "
                + (" ".join(hint) if hint else "Verifique a instalação do FFmpeg/ffprobe.")
            ) from jde
        except Exception as e:
            # outras falhas (arquivo corrompido / formato não suportado)
            raise

        samples = np.array(seg.get_array_of_samples()).reshape(-1, self.ch).astype(np.float32) / 32768.0
        with self.lock:
            self.cache[key] = (samples, self.sr)
        return self.cache[key]
