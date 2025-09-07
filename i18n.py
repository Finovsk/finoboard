from __future__ import annotations
from PySide6 import QtCore

TRANSLATIONS = {
    "pt": {
        "vbcable_warn": "Dispositivo VB-Audio CABLE não foi encontrado. Instale o VB-CABLE e selecione-o como Saída no Finoboard; depois escolha o VB-CABLE como Entrada no Discord/OBS.",
        "view_label": "Visualização",
        "view_list": "Lista",
        "view_grid": "Grade",
        "mic_label": "Microfone",
        "output_label": "Saída",
        "refresh_devices": "Atualizar dispositivos",
        "volume": "Volume: {val}%",
        "mixer_enable": "Usar mixer",
        "monitor_enable": "Ouvir local",
        "monitor_label": "Monitor (alto-falantes):",
        "monitor_volume": "Vol. monitor: {val}%",
        "add_audios": "Adicionar áudio(s)",
        "stop": "Parar",
        "clear": "Limpar tudo",
        "save_preset": "Salvar preset...",
        "load_preset": "Abrir preset...",
        "devices_error": "Falha ao listar dispositivos: {err}",

        "add_files_title": "Adicionar arquivos de áudio",
        "add_files_filter": "Áudios (*.mp3 *.wav *.ogg *.flac *.m4a);;Todos (*)",
        "adding_files": "Adicionando arquivos...",
        "added_n": "Adicionados {n}/{total}",

        "cant_output": "Selecione um dispositivo de saída válido.",
        "playing": "Tocando: {name}",
        "play_error": "Falha ao tocar \"{path}\": {err}",

        "preset_save_title": "Salvar preset do Finoboard",
        "list_empty": "A lista está vazia.",
        "preset_saved": "Preset salvo em: {path}",
        "preset_open_title": "Abrir preset do Finoboard",
        "missing_files_title": "Arquivos não encontrados",
        "missing_files_msg": "Os seguintes itens não foram encontrados:\n- {items}",
        "preset_loaded": "Preset carregado: {name}",

        "conflict_title": "Hotkey já usada",
        "conflict_msg": "As seguintes combinações já estão em uso:\n{keys}",
        "hotkeys_error": "Erro nas hotkeys: {err}",
        "hotkey_title": "Definir hotkey",
        "hotkey_info": "Pressione a combinação de teclas desejada. Use 'Limpar' para remover.",
        "hotkey_clear": "Limpar",
        "ok": "OK",
        "cancel": "Cancelar",
        "no_hotkey": "sem hotkey",

        "btn_play": "Tocar",
        "tip_hotkey": "Hotkey (⌨)",
        "tip_rename": "Renomear (✎)",
        "tip_clear": "Limpar hotkey (🧹)",
        "tip_delete": "Excluir (✖)",

        "rename_title": "Renomear",
        "rename_prompt": "Novo nome para o áudio:",
        "hotkey_in_use_title": "Hotkey já usada",
        "hotkey_in_use_msg": "A hotkey \"{hk}\" já está configurada para \"{name}\".",
    },

    "en": {
        "vbcable_warn": "VB-Audio CABLE device was not found. Please install VB-CABLE and select it as the Output in Finoboard; then choose VB-CABLE as the Input in Discord/OBS.",
        "view_label": "View",
        "view_list": "List",
        "view_grid": "Grid",
        "mic_label": "Microphone",
        "output_label": "Output",
        "refresh_devices": "Refresh devices",
        "volume": "Volume: {val}%",
        "mixer_enable": "Use mixer",
        "monitor_enable": "Monitor (local)",
        "monitor_label": "Monitor device:",
        "monitor_volume": "Monitor vol.: {val}%",
        "add_audios": "Add audio(s)",
        "stop": "Stop",
        "clear": "Clear all",
        "save_preset": "Save preset...",
        "load_preset": "Open preset...",
        "devices_error": "Failed to list devices: {err}",

        "add_files_title": "Add audio files",
        "add_files_filter": "Audio (*.mp3 *.wav *.ogg *.flac *.m4a);;All (*)",
        "adding_files": "Adding files...",
        "added_n": "Added {n}/{total}",

        "cant_output": "Select a valid output device.",
        "playing": "Playing: {name}",
        "play_error": "Failed to play \"{path}\": {err}",

        "preset_save_title": "Save Finoboard preset",
        "list_empty": "List is empty.",
        "preset_saved": "Preset saved to: {path}",
        "preset_open_title": "Open Finoboard preset",
        "missing_files_title": "Missing files",
        "missing_files_msg": "These items were not found:\n- {items}",
        "preset_loaded": "Preset loaded: {name}",

        "conflict_title": "Hotkey already in use",
        "conflict_msg": "These combinations are already in use:\n{keys}",
        "hotkeys_error": "Hotkeys error: {err}",
        "hotkey_title": "Set hotkey",
        "hotkey_info": "Press the desired key combination. Use 'Clear' to remove.",
        "hotkey_clear": "Clear",
        "ok": "OK",
        "cancel": "Cancel",
        "no_hotkey": "no hotkey",

        "btn_play": "Play",
        "tip_hotkey": "Hotkey (⌨)",
        "tip_rename": "Rename (✎)",
        "tip_clear": "Clear hotkey (🧹)",
        "tip_delete": "Delete (✖)",

        "rename_title": "Rename",
        "rename_prompt": "New name for the audio:",
        "hotkey_in_use_title": "Hotkey already in use",
        "hotkey_in_use_msg": "Hotkey \"{hk}\" is already assigned to \"{name}\".",
    },

    "es": {
        "vbcable_warn": "No se encontró el dispositivo VB-Audio CABLE. Instala VB-CABLE y selecciónalo como Salida en Finoboard; luego elige VB-CABLE como Entrada en Discord/OBS.",
        "view_label": "Vista",
        "view_list": "Lista",
        "view_grid": "Cuadrícula",
        "mic_label": "Micrófono",
        "output_label": "Salida",
        "refresh_devices": "Actualizar dispositivos",
        "volume": "Volumen: {val}%",
        "mixer_enable": "Usar mezclador",
        "monitor_enable": "Monitorear local",
        "monitor_label": "Dispositivo de monitoreo:",
        "monitor_volume": "Vol. monitoreo: {val}%",
        "add_audios": "Agregar audio(s)",
        "stop": "Detener",
        "clear": "Limpiar todo",
        "save_preset": "Guardar preset...",
        "load_preset": "Abrir preset...",
        "devices_error": "Error al listar dispositivos: {err}",

        "add_files_title": "Agregar archivos de audio",
        "add_files_filter": "Audio (*.mp3 *.wav *.ogg *.flac *.m4a);;Todos (*)",
        "adding_files": "Agregando archivos...",
        "added_n": "Agregados {n}/{total}",

        "cant_output": "Seleccione un dispositivo de salida válido.",
        "playing": "Reproduciendo: {name}",
        "play_error": "Error al reproducir \"{path}\": {err}",

        "preset_save_title": "Guardar preset de Finoboard",
        "list_empty": "La lista está vacía.",
        "preset_saved": "Preset guardado en: {path}",
        "preset_open_title": "Abrir preset de Finoboard",
        "missing_files_title": "Archivos faltantes",
        "missing_files_msg": "No se encontraron estos elementos:\n- {items}",
        "preset_loaded": "Preset cargado: {name}",

        "conflict_title": "Hotkey en uso",
        "conflict_msg": "Estas combinaciones ya están en uso:\n{keys}",
        "hotkeys_error": "Error de hotkeys: {err}",
        "hotkey_title": "Definir hotkey",
        "hotkey_info": "Presione la combinación deseada. Use 'Limpiar' para quitar.",
        "hotkey_clear": "Limpiar",
        "ok": "OK",
        "cancel": "Cancelar",
        "no_hotkey": "sin hotkey",

        "btn_play": "Reproducir",
        "tip_hotkey": "Hotkey (⌨)",
        "tip_rename": "Renombrar (✎)",
        "tip_clear": "Limpiar hotkey (🧹)",
        "tip_delete": "Eliminar (✖)",

        "rename_title": "Renombrar",
        "rename_prompt": "Nuevo nombre para el audio:",
        "hotkey_in_use_title": "Hotkey en uso",
        "hotkey_in_use_msg": "La hotkey \"{hk}\" ya está asignada a \"{name}\".",
    },

    "ja": {
        "vbcable_warn": "VB-Audio CABLE デバイスが見つかりませんでした。VB-CABLE をインストールし、Finoboard で出力として選択してください。その後、Discord/OBS では入力として VB-CABLE を選びます。",
        "view_label": "表示",
        "view_list": "リスト",
        "view_grid": "グリッド",
        "mic_label": "マイク",
        "output_label": "出力",
        "refresh_devices": "デバイスを更新",
        "volume": "音量: {val}%",
        "mixer_enable": "ミキサーを使用",
        "monitor_enable": "ローカルモニター",
        "monitor_label": "モニター デバイス:",
        "monitor_volume": "モニター音量: {val}%",
        "add_audios": "音声を追加",
        "stop": "停止",
        "clear": "すべてクリア",
        "save_preset": "プリセットを保存...",
        "load_preset": "プリセットを開く...",
        "devices_error": "デバイスの取得に失敗: {err}",

        "add_files_title": "音声ファイルを追加",
        "add_files_filter": "オーディオ (*.mp3 *.wav *.ogg *.flac *.m4a);;すべて (*)",
        "adding_files": "追加中...",
        "added_n": "{total} 中 {n} を追加",

        "cant_output": "有効な出力デバイスを選択してください。",
        "playing": "再生中: {name}",
        "play_error": "再生に失敗 \"{path}\": {err}",

        "preset_save_title": "Finoboard プリセットの保存",
        "list_empty": "リストは空です。",
        "preset_saved": "プリセットを保存しました: {path}",
        "preset_open_title": "Finoboard プリセットを開く",
        "missing_files_title": "見つからないファイル",
        "missing_files_msg": "次の項目が見つかりませんでした:\n- {items}",
        "preset_loaded": "プリセットを読み込みました: {name}",

        "conflict_title": "ホットキーが使用中",
        "conflict_msg": "次の組み合わせは使用中です:\n{keys}",
        "hotkeys_error": "ホットキーエラー: {err}",
        "hotkey_title": "ホットキーを設定",
        "hotkey_info": "目的のキーの組み合わせを押してください。「クリア」で削除します。",
        "hotkey_clear": "クリア",
        "ok": "OK",
        "cancel": "キャンセル",
        "no_hotkey": "ホットキーなし",

        "btn_play": "再生",
        "tip_hotkey": "ホットキー (⌨)",
        "tip_rename": "名前を変更 (✎)",
        "tip_clear": "ホットキーをクリア (🧹)",
        "tip_delete": "削除 (✖)",

        "rename_title": "名前の変更",
        "rename_prompt": "音声の新しい名前:",
        "hotkey_in_use_title": "ホットキーが使用中",
        "hotkey_in_use_msg": "ホットキー「{hk}」はすでに「{name}」に割り当てられています。",
    },

    "zh": {
        "vbcable_warn": "未检测到 VB-Audio CABLE 设备。请安装 VB-CABLE，并在 Finoboard 中将其设置为输出；随后在 Discord/OBS 中将 VB-CABLE 设为输入。",
        "view_label": "视图",
        "view_list": "列表",
        "view_grid": "网格",
        "mic_label": "麦克风",
        "output_label": "输出",
        "refresh_devices": "刷新设备",
        "volume": "音量: {val}%",
        "mixer_enable": "使用混音器",
        "monitor_enable": "本地监听",
        "monitor_label": "监听设备：",
        "monitor_volume": "监听音量: {val}%",
        "add_audios": "添加音频",
        "stop": "停止",
        "clear": "全部清除",
        "save_preset": "保存预设...",
        "load_preset": "打开预设...",
        "devices_error": "列出设备失败: {err}",

        "add_files_title": "添加音频文件",
        "add_files_filter": "音频 (*.mp3 *.wav *.ogg *.flac *.m4a);;所有 (*)",
        "adding_files": "正在添加文件...",
        "added_n": "已添加 {n}/{total}",

        "cant_output": "请选择有效的输出设备。",
        "playing": "正在播放: {name}",
        "play_error": "播放失败 \"{path}\": {err}",

        "preset_save_title": "保存 Finoboard 预设",
        "list_empty": "列表为空。",
        "preset_saved": "预设已保存: {path}",
        "preset_open_title": "打开 Finoboard 预设",
        "missing_files_title": "缺少文件",
        "missing_files_msg": "未找到以下项目：\n- {items}",
        "preset_loaded": "已加载预设: {name}",

        "conflict_title": "热键已被使用",
        "conflict_msg": "这些组合已被使用：\n{keys}",
        "hotkeys_error": "热键错误: {err}",
        "hotkey_title": "设置热键",
        "hotkey_info": "请按下想要的组合。使用“清除”来移除。",
        "hotkey_clear": "清除",
        "ok": "确定",
        "cancel": "取消",
        "no_hotkey": "无热键",

        "btn_play": "播放",
        "tip_hotkey": "热键 (⌨)",
        "tip_rename": "重命名 (✎)",
        "tip_clear": "清除热键 (🧹)",
        "tip_delete": "删除 (✖)",

        "rename_title": "重命名",
        "rename_prompt": "音频的新名称：",
        "hotkey_in_use_title": "热键已被使用",
        "hotkey_in_use_msg": "热键“{hk}”已分配给“{name}”。",
    },
}

class Translator(QtCore.QObject):
    languageChanged = QtCore.Signal()

    def __init__(self, lang: str = "pt"):
        super().__init__()
        self.lang = lang

    def set_language(self, lang: str):
        if lang in TRANSLATIONS and lang != self.lang:
            self.lang = lang
            self.languageChanged.emit()

    def t(self, key: str, **kwargs) -> str:
        table = TRANSLATIONS.get(self.lang) or TRANSLATIONS["pt"]
        text = table.get(key)
        if text is None:
            text = TRANSLATIONS["en"].get(key, key)
        try:
            return text.format(**kwargs)
        except Exception:
            return text
