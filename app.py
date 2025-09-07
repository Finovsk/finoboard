import sys, os, json, threading, shutil
import resources_rc
import sounddevice as sd
from PySide6 import QtCore, QtWidgets, QtGui
import concurrent.futures

from i18n import Translator, TRANSLATIONS
from mixer import Mixer
from audio_cache import AudioCache
from widgets import SoundItemWidget, SoundCardWidget, CardsPanel, ElidedLabel
from hotkeys import HotkeyManager

PRESET_FILTER = "Preset do Finoboard (*.finoboard.json);;JSON (*.json);;Todos (*)"
AUDIO_EXTS = (".mp3", ".wav", ".ogg", ".flac", ".m4a")

def _safe_disconnect(signal, slot):
    try:
        signal.disconnect(slot)
    except (TypeError, RuntimeError):
        pass

def _resource_path(relpath: str) -> str:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, relpath)

# ---------- Pydub / FFmpeg ----------
from pydub import AudioSegment

def _ensure_ffmpeg_ffprobe():
    set_from=[]
    local_ffmpeg=_resource_path("ffmpeg.exe")
    local_ffprobe=_resource_path("ffprobe.exe")
    if os.path.exists(local_ffmpeg):
        AudioSegment.converter=local_ffmpeg; set_from.append(local_ffmpeg)
    if os.path.exists(local_ffprobe):
        AudioSegment.ffprobe=local_ffprobe; set_from.append(local_ffprobe)

    if not getattr(AudioSegment,"converter",None):
        ffm=shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        if ffm: AudioSegment.converter=ffm; set_from.append(ffm)
    if not getattr(AudioSegment,"ffprobe",None):
        ffp=shutil.which("ffprobe") or shutil.which("ffprobe.exe")
        if ffp: AudioSegment.ffprobe=ffp; set_from.append(ffp)

    choco_bin = r"C:\ProgramData\chocolatey\bin"
    if os.name=="nt" and os.path.isdir(choco_bin):
        if not getattr(AudioSegment,"converter",None):
            ffm=os.path.join(choco_bin,"ffmpeg.exe")
            if os.path.exists(ffm): AudioSegment.converter=ffm; set_from.append(ffm)
        if not getattr(AudioSegment,"ffprobe",None):
            ffp=os.path.join(choco_bin,"ffprobe.exe")
            if os.path.exists(ffp): AudioSegment.ffprobe=ffp; set_from.append(ffp)
    return set_from

# --- esconder janelas ffmpeg/ffprobe ---
import subprocess as _subprocess, pydub.utils as _pydub_utils
if sys.platform == "win32":
    _orig_pydub_popen = _pydub_utils.Popen
    def _quiet_pydub_popen(*args, **kwargs):
        si = kwargs.get("startupinfo") or _subprocess.STARTUPINFO()
        si.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kwargs["startupinfo"] = si
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | _subprocess.CREATE_NO_WINDOW
        return _orig_pydub_popen(*args, **kwargs)
    _pydub_utils.Popen = _quiet_pydub_popen

    _orig_subproc_popen = _subprocess.Popen
    def _quiet_subproc_popen(cmd, *args, **kwargs):
        def _is_ff(path: str) -> bool:
            p = (path or "").lower()
            return p.endswith("ffmpeg.exe") or p.endswith("ffprobe.exe") or p.endswith("ffmpeg") or p.endswith("ffprobe")
        try:
            first = cmd[0] if isinstance(cmd, (list, tuple)) else cmd
        except Exception:
            first = None
        if _is_ff(str(first)):
            si = kwargs.get("startupinfo") or _subprocess.STARTUPINFO()
            si.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            kwargs["startupinfo"] = si
            kwargs["creationflags"] = kwargs.get("creationflags", 0) | _subprocess.CREATE_NO_WINDOW
        return _orig_subproc_popen(cmd, *args, **kwargs)
    _subprocess.Popen = _quiet_subproc_popen
# --------------------------------------

class SoundboardApp(QtWidgets.QMainWindow):
    sig_add_path=QtCore.Signal(str)
    sig_status=QtCore.Signal(str,int)
    sig_bulk_done=QtCore.Signal()
    sig_progress_text=QtCore.Signal(str)
    sig_progress_value=QtCore.Signal(int)
    sig_progress_close=QtCore.Signal()

    ROW_HEIGHT = 112

    def __init__(self):
        super().__init__()
        self.tr=Translator("pt")
        self.mixer=Mixer(samplerate=48000, channels=2, blocksize=256)
        self.cache=AudioCache(target_samplerate=self.mixer.sr, target_channels=2)
        self.gain=1.0; self.monitor_gain=1.0
        self.hk=HotkeyManager()
        self.view_mode="grid"

        self.sig_add_path.connect(self._add_item_from_signal)
        self.sig_status.connect(self._show_status)
        self.sig_bulk_done.connect(self.after_bulk_add)

        self._progress_add = None

        self._build_ui()
        self.tr.languageChanged.connect(self._retranslate)

        set_from=_ensure_ffmpeg_ffprobe()
        ffm = getattr(AudioSegment, "converter", None)
        ffp = getattr(AudioSegment, "ffprobe", None)
        if ffm and ffp:
            where=", ".join(set_from) if set_from else "PATH do sistema"
            self.status.showMessage(f"FFmpeg/ffprobe OK ({where})",6000)
        else:
            self.status.showMessage("FFmpeg/ffprobe não encontrados. MP3/M4A podem falhar.",8000)

        self.fill_devices()

        icon = QtGui.QIcon(":/icons/finoboard.ico")
        self.setWindowIcon(icon)

        self.rebuild_hotkeys()
        self.apply_view_mode()

    # ---------- assets / estilos ----------
    def _ensure_check_asset(self) -> str:
        pal = self.palette()
        color = pal.color(QtGui.QPalette.ColorRole.Text).name() if hasattr(QtGui.QPalette, "ColorRole") else "#ffffff"

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24">
    <path fill="none" stroke="{color}" stroke-width="2" d="M4 12l5 5 11-11"/>
    </svg>"""

        tmpdir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.TempLocation)
        os.makedirs(tmpdir, exist_ok=True)
        path = os.path.join(tmpdir, "finoboard_check.svg")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)
        except Exception:
            # fallback bem simples
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg.replace(color, "#ffffff"))
        return path.replace("\\", "/")


    def _ensure_arrow_asset(self) -> str:
        pal = self.palette()
        color = pal.color(QtGui.QPalette.ColorRole.Text).name() if hasattr(QtGui.QPalette, "ColorRole") else "#dddddd"

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24">
    <path fill="{color}" d="M7 10l5 5 5-5z"/>
    </svg>"""

        tmpdir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.TempLocation)
        os.makedirs(tmpdir, exist_ok=True)
        path = os.path.join(tmpdir, "finoboard_arrow.svg")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)
        except Exception:
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg.replace(color, "#dddddd"))
        return path.replace("\\", "/")


    def _apply_global_styles(self):
        check_url = self._ensure_check_asset()
        arrow_url = self._ensure_arrow_asset()

        self.setStyleSheet(f"""
            QWidget {{ background: #141419; color: #e8e8ea; }}
            QScrollArea, QListWidget {{ background: transparent; }}

            QFrame#RowCard {{
                background: #1c1b22;
                border: 1px solid #3a3450;
                border-radius: 16px;
            }}
            QFrame#RowCard:hover {{
                border: 1px solid #8b6cf8;
                background: #1f1d28;
            }}

            QFrame#Card {{
                background: #1c1b22;
                border: 1px solid #3a3450;
                border-radius: 18px;
            }}
            QFrame#Card:hover {{
                border: 1px solid #8b6cf8;
                background: #1f1d28;
            }}

            QPushButton {{
                min-height: 30px;
                padding: 4px 12px;
                font-size: 11pt;
                color: #ececf1;
                background: #23222b;
                border: 1px solid #3a3450;
                border-radius: 10px;
            }}
            QPushButton:hover {{ background: #2a2934; border-color: #8b6cf8; }}
            QPushButton:pressed {{ background: #242231; }}

            QPushButton#BtnPlayList {{ font-size: 14pt; min-height: 38px; background: #2a2934; }}
            QPushButton#BigPlay    {{ font-size: 18pt; min-height: 56px; background: #2a2934;
                                    border: 1px solid #3a3450; border-radius: 12px; }}
            QPushButton#BigPlay:hover {{ border-color: #8b6cf8; }}

            QToolButton {{
                min-width: 36px; min-height: 36px; color: #ddd; background: #23222b;
                border: 1px solid #3a3450; border-radius: 10px;
            }}
            QToolButton:hover {{ background: #2a2934; border-color: #8b6cf8; }}
            QToolButton:pressed {{ background: #242231; }}

            /* ---- ComboBoxes ---- */
            QComboBox {{
                min-height: 30px; padding: 2px 8px;
                background: #1c1b22; border: 1px solid #3a3450; border-radius: 10px;
            }}
            QComboBox:hover {{ border-color: #8b6cf8; }}
            QComboBox::drop-down {{
                subcontrol-origin: padding; subcontrol-position: top right;
                width: 28px; border-left: 1px solid #3a3450;
                border-top-right-radius: 10px; border-bottom-right-radius: 10px;
                background: #1a1920;
            }}
            QComboBox::down-arrow {{
                image: url('{arrow_url}');
                width: 12px; height: 12px;
            }}

            /* ---- Checkboxes ---- */
            QCheckBox {{
                min-height: 30px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                margin: 0 8px 0 2px;       /* espaço entre a caixinha e o texto */
                border-radius: 5px;
                border: 1px solid #3a3450;
                background: #201f28;
            }}
            QCheckBox::indicator:unchecked {{
                width: 18px; height: 18px;
                border-radius: 5px;
                border: 1px solid #3a3450;
                background: #201f28;
            }}
            QCheckBox::indicator:checked {{
                width: 18px; height: 18px;
                border-radius: 5px;
                background: #8b6cf8;
                border: 1px solid #8b6cf8;
                image: url('{check_url}');
            }}
            QCheckBox::indicator:hover {{
                border-color: #8b6cf8;
            }}
            QCheckBox::indicator:disabled {{
                width: 18px; height: 18px;
                border-radius: 5px;
                border: 1px solid #555;
                background: #2a2934;
            }}

            QLabel#Badge {{
                background: #2c2840; color: #eae6ff; border-radius: 8px;
                padding: 2px 8px; font-size: 10pt;
            }}

            QStatusBar {{ font-size: 10pt; background: #141419; border-top: 1px solid #2a2638; }}
            QListWidget {{ outline: none; }}

            QLabel#WarnBanner {{
                background: rgba(255, 196, 0, 0.12);
                border: 1px solid rgba(255, 196, 0, 0.35);
                color: #ffd166;
                padding: 8px 10px;
                border-radius: 8px;
                font-size: 10.5pt;
            }}
        """)

    # ---------- UI ----------
    def _build_ui(self):
        self._apply_global_styles()
        self.setWindowTitle("Finoboard")
        self.resize(1280, 820)

        central=QtWidgets.QWidget(); self.setCentralWidget(central)
        root=QtWidgets.QVBoxLayout(central)

        # linha 1 (topo): Idioma + Visualização
        lineTop = QtWidgets.QHBoxLayout()
        self.langCombo = QtWidgets.QComboBox()
        self.langCombo.addItems(["Português","English","Español","日本語","简体中文"])
        self.langCombo.setItemData(0,"pt"); self.langCombo.setItemData(1,"en")
        self.langCombo.setItemData(2,"es"); self.langCombo.setItemData(3,"ja"); self.langCombo.setItemData(4,"zh")
        self.langCombo.currentIndexChanged.connect(self.on_lang_changed)

        self.viewLabel = QtWidgets.QLabel(); self.viewCombo = QtWidgets.QComboBox()
        self.viewCombo.addItem("Lista","list"); self.viewCombo.addItem("Grade","grid")
        self.viewCombo.currentIndexChanged.connect(self.on_view_changed)
        self.viewCombo.setCurrentIndex(1)

        lineTop.addWidget(QtWidgets.QLabel("🌐"))
        lineTop.addWidget(self.langCombo)
        lineTop.addSpacing(8)
        lineTop.addWidget(self.viewLabel)
        lineTop.addWidget(self.viewCombo)
        lineTop.addStretch(1)
        root.addLayout(lineTop)

        # --- linha do MIXER: "Usar mixer" + (Mic, Saída, Atualizar, Volume) ---
        lineMixer = QtWidgets.QHBoxLayout()

        # Botão "Usar mixer"
        self.mixerEnable = QtWidgets.QCheckBox(self.tr.t("mixer_enable"))
        self.mixerEnable.setChecked(True)
        self.mixerEnable.toggled.connect(self.on_mixer_toggled)
        lineMixer.addWidget(self.mixerEnable)

        # Container colapsável do mixer
        self.mixerBox = QtWidgets.QWidget()
        mx = QtWidgets.QHBoxLayout(self.mixerBox)
        mx.setContentsMargins(12, 0, 0, 0)
        mx.setSpacing(8)

        # (reaproveita os widgets já existentes)
        self.micLabel = QtWidgets.QLabel()
        self.micCombo = QtWidgets.QComboBox()
        self.outLabel = QtWidgets.QLabel()
        self.deviceCombo = QtWidgets.QComboBox()
        self.refreshBtn = QtWidgets.QPushButton()

        self.volumeLabel = QtWidgets.QLabel()
        self.volumeSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.volumeSlider.setRange(0, 200)
        self.volumeSlider.setValue(100)
        self.volumeSlider.setFixedWidth(200)
        self.volumeSlider.valueChanged.connect(self.on_volume_changed)

        # monta a linha interna
        mx.addWidget(self.micLabel);   mx.addWidget(self.micCombo,   1)
        mx.addWidget(self.outLabel);   mx.addWidget(self.deviceCombo, 1)
        mx.addWidget(self.refreshBtn)
        mx.addSpacing(10)
        mx.addWidget(self.volumeLabel); mx.addWidget(self.volumeSlider)

        # começa visível (porque "Usar mixer" vem marcado)
        self.mixerBox.setVisible(True)

        # adiciona na linha principal do mixer
        lineMixer.addWidget(self.mixerBox, 1)
        # placeholder para manter a altura quando mixerBox estiver oculto
        row_h = max(30, self.micCombo.sizeHint().height(), self.deviceCombo.sizeHint().height())
        self.mixerPlaceholder = QtWidgets.QWidget()
        self.mixerPlaceholder.setMinimumHeight(row_h)
        self.mixerPlaceholder.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.mixerPlaceholder.setVisible(False)  # mixer começa marcado, então placeholder oculto
        lineMixer.addWidget(self.mixerPlaceholder, 1)


        # empilha a linha do mixer no layout raiz
        root.addLayout(lineMixer)

        # banner VB-CABLE
        self.vbcableBanner = QtWidgets.QFrame()
        self.vbcableBanner.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.vbcableBanner.setStyleSheet("""
            QFrame {
                background: #231f2f;
                border: 1px solid #3b2f55;
                border-radius: 10px;
                color: #e9e4ff;
            }
        """)
        bnl = QtWidgets.QHBoxLayout(self.vbcableBanner)
        bnl.setContentsMargins(12, 8, 12, 8)
        self.vbcableLabel = QtWidgets.QLabel("")
        self.vbcableLabel.setWordWrap(True)
        bnl.addWidget(self.vbcableLabel, 1)
        root.addWidget(self.vbcableBanner)
        self.vbcableBanner.setVisible(False)

        # linha 2 — Ouvir local com container colapsável
        line2=QtWidgets.QHBoxLayout()
        self.monitorEnable=QtWidgets.QCheckBox(self.tr.t("monitor_enable"))
        self.monitorEnable.toggled.connect(self.on_monitor_toggled)
        line2.addWidget(self.monitorEnable)

        self.monitorBox = QtWidgets.QWidget()
        mbox = QtWidgets.QHBoxLayout(self.monitorBox)
        mbox.setContentsMargins(12, 0, 0, 0)
        mbox.setSpacing(8)
        self.monitorLabel=QtWidgets.QLabel(); self.monitorCombo=QtWidgets.QComboBox()
        self.monitorCombo.currentIndexChanged.connect(self.on_monitor_device_changed)
        self.monitorVolLabel=QtWidgets.QLabel()
        self.monitorSlider=QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.monitorSlider.setRange(0,200); self.monitorSlider.setValue(100); self.monitorSlider.setFixedWidth(200)
        self.monitorSlider.valueChanged.connect(self.on_monitor_volume_changed)
        mbox.addWidget(self.monitorLabel); mbox.addWidget(self.monitorCombo,1)
        mbox.addWidget(self.monitorVolLabel); mbox.addWidget(self.monitorSlider)
        self.monitorBox.setVisible(False)
        line2.addWidget(self.monitorBox,1)
        # placeholder para manter a altura quando monitorBox estiver oculto
        row2_h = max(30, self.monitorCombo.sizeHint().height(), self.monitorSlider.sizeHint().height())
        self.monitorPlaceholder = QtWidgets.QWidget()
        self.monitorPlaceholder.setMinimumHeight(row2_h)
        self.monitorPlaceholder.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.monitorPlaceholder.setVisible(True)   # monitor começa desmarcado
        line2.addWidget(self.monitorPlaceholder, 1)

        root.addLayout(line2)

        # stack: lista/grade
        self.stack=QtWidgets.QStackedWidget()
        self.listWidget=QtWidgets.QListWidget()
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.listWidget.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.listWidget.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.listWidget.setFlow(QtWidgets.QListView.Flow.TopToBottom)
        self.listWidget.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.listWidget.setSpacing(10)
        self.listWidget.setUniformItemSizes(False)
        self.listWidget.setAlternatingRowColors(False)
        self.listWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.stack.addWidget(self.listWidget)

        self.cardsPanel=CardsPanel(self.tr); self.stack.addWidget(self.cardsPanel)
        root.addWidget(self.stack,1)

        # bottom buttons
        buttons=QtWidgets.QHBoxLayout()
        self.addBtn=QtWidgets.QPushButton(); self.loadPresetBtn=QtWidgets.QPushButton(); self.savePresetBtn=QtWidgets.QPushButton()
        self.stopBtn=QtWidgets.QPushButton(); self.clearBtn=QtWidgets.QPushButton()
        self.addBtn.clicked.connect(self.on_add_dialog)
        self.stopBtn.clicked.connect(self.on_stop_all)
        self.clearBtn.clicked.connect(self.on_clear)
        self.refreshBtn.clicked.connect(self.fill_devices)
        self.savePresetBtn.clicked.connect(self.on_save_preset)
        self.loadPresetBtn.clicked.connect(self.on_load_preset)
        buttons.addWidget(self.addBtn); buttons.addWidget(self.loadPresetBtn); buttons.addWidget(self.savePresetBtn)
        buttons.addStretch(1); buttons.addWidget(self.stopBtn); buttons.addWidget(self.clearBtn)
        root.addLayout(buttons)

        self.status=QtWidgets.QStatusBar(); self.setStatusBar(self.status)
        self.warnLabel = QtWidgets.QLabel("")
        self.warnLabel.setObjectName("WarnBanner")
        self.warnLabel.setWordWrap(True)
        self.warnLabel.setVisible(False)
        self.findChild(QtWidgets.QVBoxLayout).insertWidget(1, self.warnLabel)
        self._retranslate()
        self.setAcceptDrops(True)

    # --- Drag & Drop ---
    def dragEnterEvent(self,e:QtGui.QDragEnterEvent):
        if e.mimeData().hasUrls(): e.acceptProposedAction()

    def dropEvent(self, e: QtGui.QDropEvent):
        from pathlib import Path
        paths = []
        for url in e.mimeData().urls():
            p = url.toLocalFile() or url.path()
            if not p: continue
            p = Path(p)
            if p.is_dir():
                for sub in p.rglob("*"):
                    if sub.is_file() and sub.suffix.lower() in AUDIO_EXTS:
                        paths.append(str(sub))
            else:
                if p.is_file() and p.suffix.lower() in AUDIO_EXTS:
                    paths.append(str(p))
        if paths:
            self.add_many_async(paths)

    # --- I18N ---
    def on_lang_changed(self): self.tr.set_language(self.langCombo.currentData())
    def _retranslate(self):
        self.setWindowTitle("Finoboard")
        self.viewLabel.setText(self.tr.t("view_label"))
        self.viewCombo.setItemText(0,self.tr.t("view_list")); self.viewCombo.setItemText(1,self.tr.t("view_grid"))
        self.micLabel.setText(self.tr.t("mic_label")); self.outLabel.setText(self.tr.t("output_label")); self.refreshBtn.setText(self.tr.t("refresh_devices"))
        self.volumeLabel.setText(self.tr.t("volume",val=self.volumeSlider.value()))
        self.monitorEnable.setText(self.tr.t("monitor_enable"))
        self.monitorLabel.setText(self.tr.t("monitor_label"))
        self.monitorVolLabel.setText(self.tr.t("monitor_volume", val=self.monitorSlider.value()))
        self.addBtn.setText(self.tr.t("add_audios")); self.stopBtn.setText(self.tr.t("stop"))
        self.clearBtn.setText(self.tr.t("clear")); self.savePresetBtn.setText(self.tr.t("save_preset")); self.loadPresetBtn.setText(self.tr.t("load_preset"))
        
        if hasattr(self, "mixerEnable"):
            self.mixerEnable.setText(self.tr.t("mixer_enable"))
        if hasattr(self, "micLabel"):
            self.micLabel.setText(self.tr.t("mic_label"))
        if hasattr(self, "outLabel"):
            self.outLabel.setText(self.tr.t("output_label"))
        if hasattr(self, "refreshBtn"):
            self.refreshBtn.setText(self.tr.t("refresh_devices"))
        if hasattr(self, "volumeLabel"):
            self.volumeLabel.setText(self.tr.t("volume", val=int(self.gain*100)))
        
        for i in range(self.listWidget.count()):
            w=self.listWidget.itemWidget(self.listWidget.item(i))
            if isinstance(w,SoundItemWidget): w._retranslate()
        self.rebuild_cards()

        # banner msg na língua
        msg = self.tr.t("vbcable_warn")
        if msg == "vbcable_warn":
            msg = "Dispositivo VB-Audio Cable não foi encontrado. Instale e selecione o VB-CABLE como Saída (no app) e como Entrada no Discord/OBS."
        self.vbcableLabel.setText(msg)

    # --- Dispositivos e volume ---
    def on_volume_changed(self,val):
        self.gain=max(0.0,val/100.0); self.volumeLabel.setText(self.tr.t("volume",val=val))
        self.mixer.gain = self.gain
    def on_monitor_volume_changed(self,val):
        self.monitor_gain=max(0.0,val/100.0)
        self.monitorVolLabel.setText(self.tr.t("monitor_volume", val=val))
        self.mixer.monitor_gain = self.monitor_gain

    def _update_vbcable_banner(self, devices_list):
        found_out = False; found_in = False
        for d in (devices_list or []):
            name = (d.get("name") or "").lower()
            if "cable" in name and "vb-audio" in name:
                if d.get("max_output_channels",0) > 0: found_out = True
                if d.get("max_input_channels",0)  > 0: found_in  = True
        self.vbcableBanner.setVisible(not (found_out and found_in))

    def fill_devices(self):
        self.micCombo.blockSignals(True); self.deviceCombo.blockSignals(True); self.monitorCombo.blockSignals(True)
        self.micCombo.clear(); self.deviceCombo.clear(); self.monitorCombo.clear()
        devices=[]
        try:
            devices=sd.query_devices()
            for idx,d in enumerate(devices):
                name=f"[{idx}] {d['name']}"
                if d['max_input_channels']>0:
                    self.micCombo.addItem(name, userData=idx)
                if d['max_output_channels']>0:
                    self.deviceCombo.addItem(name, userData=idx)
                    self.monitorCombo.addItem(name, userData=idx)
            if self.micCombo.count()==0: self.micCombo.addItem("(sem microfone)", userData=None)
            if self.deviceCombo.count()==0: self.deviceCombo.addItem("(sem saída)", userData=None)
            if self.monitorCombo.count()==0: self.monitorCombo.addItem("(sem saída)", userData=None)
        except Exception as e:
            self.status.showMessage(self.tr.t("devices_error",err=e),5000)
        self.micCombo.blockSignals(False); self.deviceCombo.blockSignals(False); self.monitorCombo.blockSignals(False)

        if not hasattr(self, "_dev_signals_connected"):
            self.micCombo.currentIndexChanged.connect(self.on_device_changed)
            self.deviceCombo.currentIndexChanged.connect(self.on_device_changed)
            self._dev_signals_connected=True
        self.on_device_changed()

        self._update_vbcable_banner(devices)

    def on_device_changed(self):
        in_idx = self.micCombo.currentData()
        out_idx = self.deviceCombo.currentData()
        self.mixer.set_devices(in_idx, out_idx, self.mixer.mon_dev)
        self.cache.set_target(self.mixer.sr, 2)

    def on_mixer_toggled(self, checked: bool):
        if hasattr(self, "mixerPlaceholder"):
            self.mixerPlaceholder.setVisible(not checked)
        # só esconde/mostra a linha do mixer
        # (não altera dispositivos nem para/religa streams)
        self.mixerBox.setVisible(checked)

    def on_monitor_toggled(self, enabled: bool):
        if hasattr(self, "monitorPlaceholder"):
            self.monitorPlaceholder.setVisible(not enabled)
        self.monitorBox.setVisible(enabled)
        mon_idx = self.monitorCombo.currentData() if enabled else None
        self.mixer.set_monitor_device(mon_idx)
    def on_monitor_device_changed(self):
        if self.monitorEnable.isChecked():
            self.mixer.set_monitor_device(self.monitorCombo.currentData())

    # --- View ---
    def on_view_changed(self):
        self.view_mode=self.viewCombo.currentData()
        if hasattr(self, "stack"):
            self.apply_view_mode()
    def apply_view_mode(self):
        if self.view_mode=="grid":
            self.stack.setCurrentWidget(self.cardsPanel); self.rebuild_cards()
        else:
            self.stack.setCurrentWidget(self.listWidget)

    def _save_restore_scroll(self):
        if self.stack.currentWidget() is self.cardsPanel:
            bar = self.cardsPanel.verticalScrollBar()
        else:
            bar = self.listWidget.verticalScrollBar()
        val = bar.value()
        def restore(): QtCore.QTimer.singleShot(0, lambda: bar.setValue(val))
        return restore

    def rebuild_cards(self):
        restore = self._save_restore_scroll()
        cards=[]
        for i in range(self.listWidget.count()):
            w=self.listWidget.itemWidget(self.listWidget.item(i))
            if not isinstance(w,SoundItemWidget): continue
            c=SoundCardWidget(self.tr,w.path,w.display_name,w.hotkey)
            c.playClicked.connect(self.on_play_path)
            c.removeClicked.connect(lambda w=w: self._remove_by_widget(w))
            c.renameClicked.connect(lambda new,w=w: self._rename_by_widget(w,new))
            c.hotkeyChanged.connect(lambda hk,w=w: self._hotkey_changed_by_widget(w,hk))
            cards.append(c)
        self.cardsPanel.set_cards(cards)
        restore()

    def find_hotkey_conflict(self, hk: str, exclude_widget: SoundItemWidget | None):
        if not hk: return None
        for i in range(self.listWidget.count()):
            w=self.listWidget.itemWidget(self.listWidget.item(i))
            if not isinstance(w,SoundItemWidget): continue
            if w is exclude_widget: continue
            if (w.hotkey or "") == hk:
                return w.display_name
        return None

    def _remove_by_widget(self,w:SoundItemWidget):
        restore = self._save_restore_scroll()
        for i in range(self.listWidget.count()):
            if self.listWidget.itemWidget(self.listWidget.item(i)) is w:
                self.listWidget.takeItem(i); break
        self.rebuild_hotkeys(); self.rebuild_cards(); restore()

    def _rename_by_widget(self,w:SoundItemWidget,newname:str):
        restore = self._save_restore_scroll()
        w.display_name=newname; self.rebuild_cards(); restore()

    def _hotkey_changed_by_widget(self,w:SoundItemWidget,new_hk:str):
        conflict = self.find_hotkey_conflict(new_hk, w)
        if conflict:
            QtWidgets.QMessageBox.warning(self, self.tr.t("hotkey_in_use_title"),
                                          self.tr.t("hotkey_in_use_msg", hk=new_hk, name=conflict))
            self.rebuild_cards()
            return
        w.set_hotkey(new_hk)
        self.rebuild_hotkeys()
        self.rebuild_cards()

    def _iter_audio_paths(self):
        paths = []
        for i in range(self.listWidget.count()):
            w = self.listWidget.itemWidget(self.listWidget.item(i))
            if isinstance(w, SoundItemWidget) and w.path:
                paths.append(w.path)
        return paths

    def _start_cache_warmup(self):
        # 2 workers evita CPU/IO exagerados e mantém UI fluida
        paths = self._iter_audio_paths()
        if not paths: return
        self._warmup_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        for p in paths:
            self._warmup_pool.submit(self._safe_cache_load, p)

    def _safe_cache_load(self, path: str):
        try:
            self.cache.load(path)  # usa o cache em memória existente
        except Exception:
            pass

    # --- Lista (fonte de verdade) ---
    def add_item(self, path, display_name=None, hotkey:str|None=None):
        item=QtWidgets.QListWidgetItem()
        widget=SoundItemWidget(self.tr,path,display_name=display_name,hotkey=hotkey)
        item.setSizeHint(QtCore.QSize(0, self.ROW_HEIGHT))
        self.listWidget.addItem(item); self.listWidget.setItemWidget(item,widget)
        widget.playClicked.connect(self.on_play_path)
        widget.removeClicked.connect(lambda it=item: self.remove_item(it))
        widget.renameClicked.connect(lambda _new,it=item: self.on_item_renamed(it,_new))
        widget.hotkeyChanged.connect(lambda _hk,it=item: self.on_item_hotkey_changed(it))

    @QtCore.Slot(str)
    def _add_item_from_signal(self,path:str): self.add_item(path)

    def on_item_renamed(self,item,newname):
        w=self.listWidget.itemWidget(item); w.display_name=newname
        self.rebuild_cards()

    def on_item_hotkey_changed(self,item):
        w=self.listWidget.itemWidget(item)
        conflict = self.find_hotkey_conflict(w.hotkey, w)
        if conflict:
            old = ""
            w.set_hotkey(old)
            QtWidgets.QMessageBox.warning(self, self.tr.t("hotkey_in_use_title"),
                                          self.tr.t("hotkey_in_use_msg", hk=w.hotkey, name=conflict))
            return
        self.rebuild_hotkeys()
        self.rebuild_cards()

    def remove_item(self,item):
        restore = self._save_restore_scroll()
        row=self.listWidget.row(item); self.listWidget.takeItem(row)
        self.rebuild_hotkeys(); self.rebuild_cards(); restore()
    
    # --- Adicionar arquivos ---
    def on_add_dialog(self):
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            self.tr.t("add_files_title"),
            "",
            self.tr.t("add_files_filter")
        )
        if not files:
            self.status.showMessage(self.tr.t("list_empty"), 3000)
            return
        self.add_many_async(files)

    # --- Adição em lote ---
    def add_many_async(self, paths):
        from pathlib import Path
        flat = []
        for p in paths:
            p = Path(p)
            if p.is_dir():
                for sub in p.rglob("*"):
                    if sub.is_file() and sub.suffix.lower() in AUDIO_EXTS:
                        flat.append(str(sub))
            else:
                if p.is_file() and p.suffix.lower() in AUDIO_EXTS:
                    flat.append(str(p))
        seen = set(); flat_unique=[]
        for f in flat:
            if f not in seen:
                seen.add(f); flat_unique.append(f)
        MAX_TO_ADD = 10000
        flat_unique = flat_unique[:MAX_TO_ADD]
        total = len(flat_unique)
        if total == 0:
            self.status.showMessage(self.tr.t("missing_files_title"), 4000)
            return

        self._progress_add = QtWidgets.QProgressDialog(
            self.tr.t("adding_files"), self.tr.t("stop"), 0, total, self
        )
        self._progress_add.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self._progress_add.setMinimumDuration(0)
        self._progress_add.setAutoClose(False)
        self._progress_add.setAutoReset(False)

        try: self.sig_progress_text.disconnect()
        except: pass
        try: self.sig_progress_value.disconnect()
        except: pass
        try: self.sig_progress_close.disconnect()
        except: pass
        self.sig_progress_text.connect(self._progress_add.setLabelText)
        self.sig_progress_value.connect(self._progress_add.setValue)
        self.sig_progress_close.connect(self._progress_add.close)

        def worker():
            n = 0
            try:
                for p in flat_unique:
                    if self._progress_add.wasCanceled():
                        break
                    self.sig_add_path.emit(p)
                    n += 1
                    self.sig_progress_text.emit(self.tr.t("added_n", n=n, total=total))
                    self.sig_progress_value.emit(n)
            finally:
                self.sig_progress_close.emit()
                self.sig_bulk_done.emit()
                QtCore.QTimer.singleShot(0, lambda: setattr(self, "_progress_add", None))

        threading.Thread(target=worker, daemon=True).start()

    @QtCore.Slot()
    def after_bulk_add(self):
        self.rebuild_hotkeys(); self.rebuild_cards()
        self._start_cache_warmup()

    # --- Playback (um por vez) ---
    def play_by_index(self, idx):
        if 0<=idx<self.listWidget.count():
            w=self.listWidget.itemWidget(self.listWidget.item(idx))
            self.on_play_path(w.path)

    def current_entries(self):
        entries=[]
        for i in range(self.listWidget.count()):
            w=self.listWidget.itemWidget(self.listWidget.item(i))
            entries.append({"path":w.path,"name":w.display_name,"hotkey":w.hotkey})
        return entries

    def on_play_path(self,path):
        if self.deviceCombo.currentData() is None:
            self.status.showMessage(self.tr.t("cant_output"), 4000); return
        def decode_and_play():
            try:
                data,sr=self.cache.load(path)
                if sr != self.mixer.sr:
                    self.cache.set_target(self.mixer.sr, 2)
                    data,sr=self.cache.load(path)
                self.mixer.stop_all()
                self.mixer.play_clip(data, sr)
                self.sig_status.emit(self.tr.t("playing",name=os.path.basename(path)),2000)
            except Exception as e:
                self.sig_status.emit(self.tr.t("play_error",path=os.path.basename(path),err=e),6000)
        threading.Thread(target=decode_and_play,daemon=True).start()

    def on_stop_all(self):
        self.mixer.stop_all()

    # ---------- Presets ----------
    def _select_device_by_saved(self, combo: QtWidgets.QComboBox, saved: dict):
        if not saved: return
        name = saved.get("name"); idx  = saved.get("index")
        if name:
            for i in range(combo.count()):
                if combo.itemText(i) == name:
                    combo.setCurrentIndex(i); return
        if idx is not None:
            for i in range(combo.count()):
                if combo.itemData(i) == idx:
                    combo.setCurrentIndex(i); return

    def on_save_preset(self):
        if self.listWidget.count()==0:
            QtWidgets.QMessageBox.information(self,self.tr.t("preset_save_title"),self.tr.t("list_empty")); return
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,self.tr.t("preset_save_title"),
                                                     filter=PRESET_FILTER,
                                                     selectedFilter="Preset do Finoboard (*.finoboard.json)")
        if not path: return
        if not path.lower().endswith(".json"):
            path += ".finoboard.json"

        mic_idx = self.micCombo.currentData()
        out_idx = self.deviceCombo.currentData()
        mon_idx = self.monitorCombo.currentData()
        mic_name = self.micCombo.currentText() if self.micCombo.currentIndex()>=0 else ""
        out_name = self.deviceCombo.currentText() if self.deviceCombo.currentIndex()>=0 else ""
        mon_name = self.monitorCombo.currentText() if self.monitorCombo.currentIndex()>=0 else ""

        data={
            "version": 20,
            "language": self.tr.lang,
            "view_mode": self.view_mode,
            "items": self.current_entries(),
            "devices": {
                "mic": {"index": mic_idx, "name": mic_name},
                "out": {"index": out_idx, "name": out_name},
                "monitor": {"enabled": bool(self.monitorEnable.isChecked()),
                            "index": mon_idx, "name": mon_name},
            },
            "volumes": {"main": int(self.volumeSlider.value()),
                        "monitor": int(self.monitorSlider.value())}
        }

        try:
            with open(path,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
            self.status.showMessage(self.tr.t("preset_saved",path=path),5000)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self,self.tr.t("preset_save_title"),str(e))

    def on_load_preset(self):
        path,_=QtWidgets.QFileDialog.getOpenFileName(self,self.tr.t("preset_open_title"),filter=PRESET_FILTER)
        if not path: return
        try:
            with open(path,"r",encoding="utf-8") as f: data=json.load(f)

            lang=data.get("language")
            if lang in TRANSLATIONS:
                idx=self.langCombo.findData(lang)
                if idx>=0: self.langCombo.setCurrentIndex(idx)
            vm=data.get("view_mode") or "grid"
            idx_vm=self.viewCombo.findData(vm)
            if idx_vm>=0: self.viewCombo.setCurrentIndex(idx_vm)

            self.on_clear()

            items=data.get("items",[])
            missing=[]
            for it in items:
                p=it.get("path"); n=it.get("name") or (os.path.basename(p) if p else "")
                hk=(it.get("hotkey") or "")
                if p and os.path.exists(p): self.add_item(p,display_name=n,hotkey=hk)
                else: missing.append(n or p or "(sem nome)")
            if missing:
                QtWidgets.QMessageBox.warning(self,self.tr.t("missing_files_title"),
                                              self.tr.t("missing_files_msg",items="\n- ".join(missing)))

            vols = (data.get("volumes") or {})
            if "main" in vols:
                self.volumeSlider.setValue(int(vols["main"]))
                self.on_volume_changed(self.volumeSlider.value())
            if "monitor" in vols:
                self.monitorSlider.setValue(int(vols["monitor"]))
                self.on_monitor_volume_changed(self.monitorSlider.value())

            devs = (data.get("devices") or {})
            self.fill_devices()
            self.micCombo.blockSignals(True); self.deviceCombo.blockSignals(True); self.monitorCombo.blockSignals(True)
            try:
                self._select_device_by_saved(self.micCombo, devs.get("mic") or {})
                self._select_device_by_saved(self.deviceCombo, devs.get("out") or {})
                mon_info = devs.get("monitor") or {}
                self.monitorEnable.setChecked(bool(mon_info.get("enabled", False)))
                self._select_device_by_saved(self.monitorCombo, mon_info)
            finally:
                self.micCombo.blockSignals(False); self.deviceCombo.blockSignals(False); self.monitorCombo.blockSignals(False)

            self.on_device_changed()
            if self.monitorEnable.isChecked():
                self.on_monitor_device_changed()
            else:
                self.mixer.set_monitor_device(None)

            self.status.showMessage(self.tr.t("preset_loaded",name=os.path.basename(path)),5000)
            self.apply_view_mode()
            self.rebuild_hotkeys()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self,self.tr.t("preset_open_title"),str(e))

    # --- Hotkeys globais ---
    def rebuild_hotkeys(self):
        def conflicts_cb(keys):
            QtWidgets.QMessageBox.warning(self,self.tr.t("conflict_title"),
                                          self.tr.t("conflict_msg",keys="\n- ".join(keys)))
        def error_cb(err):
            QtWidgets.QMessageBox.critical(self,"Hotkeys", self.tr.t("hotkeys_error",err=err))
        self.hk.rebuild(self.current_entries(), self.play_by_index, conflict_cb=conflicts_cb, error_cb=error_cb)

    # --- Util ---
    @QtCore.Slot(str,int)
    def _show_status(self,msg:str,timeout:int): self.status.showMessage(msg,timeout)
    def on_clear(self):
        self.on_stop_all(); self.listWidget.clear()
        self.rebuild_hotkeys(); self.rebuild_cards()
    def closeEvent(self,event:QtGui.QCloseEvent):
        try:self.hk.stop()
        finally:self.mixer.stop()
        return super().closeEvent(event)

def main():
    app=QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(":/icons/finoboard.ico"))
    win=SoundboardApp(); win.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
