import os
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE  # sem COLLECT → one-file

block_cipher = None

# === Caminhos REAIS do ffmpeg/ffprobe (não use os shims de ...\chocolatey\bin) ===
FFMPEG_REAL  = r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin\ffmpeg.exe"
FFPROBE_REAL = r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin\ffprobe.exe"

# === Plugins mínimos do Qt (PySide6) ===
import PySide6
from PySide6.QtCore import QLibraryInfo
plugins_dir = QLibraryInfo.path(QLibraryInfo.PluginsPath)

qt_binaries = []
def add_qt_plugin(relpath):
    src = os.path.join(plugins_dir, relpath)
    if os.path.exists(src):
        dst = os.path.join('PySide6', 'plugins', os.path.dirname(relpath))
        qt_binaries.append((src, dst))

# Essencial
add_qt_plugin(os.path.join('platforms', 'qwindows.dll'))
# Opcionais úteis
add_qt_plugin(os.path.join('styles', 'qwindowsvistastyle.dll'))
add_qt_plugin(os.path.join('imageformats', 'qico.dll'))
add_qt_plugin(os.path.join('imageformats', 'qjpeg.dll'))

binaries = [
    (FFMPEG_REAL,  '.'),
    (FFPROBE_REAL, '.'),
] + qt_binaries

hiddenimports = []

excludes = [
    'project_lib',
    'PySide6.scripts.deploy',
    'PySide6.scripts.deploy_lib',
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineQuick',
    'PySide6.QtPrintSupport',
    'PySide6.QtCharts',
    'PySide6.QtTest',
    'PySide6.QtSvg',
    'PySide6.QtSvgWidgets',
    'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets',
]

datas = [
    ('finoboard.ico', '.'),
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Finoboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[
        'python3.dll',
        '_uuid.pyd',
    ],
    console=False,
    disable_windowed_traceback=True,
    icon='finoboard.ico',
    runtime_tmpdir = os.path.expandvars(r"%LOCALAPPDATA%\Finoboard\_tmp")
)
