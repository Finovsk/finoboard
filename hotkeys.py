import re
from pynput.keyboard import GlobalHotKeys

HOTKEY_RE = re.compile(
    r"^\s*(?:ctrl|alt|shift|cmd|ctrl_r|alt_r|shift_r|cmd_r)(?:\+(?:ctrl|alt|shift|cmd|ctrl_r|alt_r|shift_r|cmd_r))*"
    r"(?:\+[A-Za-z0-9]|(?:\+f(?:[1-9]|1[0-2]))|(?:\+(?:space|enter|esc|tab|backspace|delete|home|end|page_up|page_down|left|right|up|down)))"
    r"|\s*(?:[A-Za-z0-9]|f(?:[1-9]|1[0-2])|space|enter|esc|tab|backspace|delete|home|end|page_up|page_down|left|right|up|down)\s*$",
    re.IGNORECASE
)
_MODS = ["ctrl","alt","shift","cmd","ctrl_r","alt_r","shift_r","cmd_r"]

def norm_hotkey(hk: str) -> str:
    if not hk: return ""
    hk = hk.strip().lower().replace("<","").replace(">","").replace(" ","").replace("++","+")
    parts = [p for p in hk.split("+") if p]
    mods = [m for m in _MODS if m in parts]
    keys = [p for p in parts if p not in _MODS]
    key  = keys[-1] if keys else ""
    ordered = mods + ([key] if key else [])
    return "+".join(ordered)

def to_pynput_combo(hk: str) -> str:
    if not hk: return ""
    parts = [p for p in hk.split("+") if p]
    mods = [m for m in _MODS if m in parts]
    keys = [p for p in parts if p not in _MODS]
    key = keys[-1] if keys else ""
    out = [f"<{m}>" for m in mods]
    if key: out.append(key)
    return "+".join(out)

class HotkeyManager:
    def __init__(self):
        self.listener = None

    def rebuild(self, entries, play_callback, conflict_cb=None, error_cb=None):
        self.stop()
        mapping = {}
        conflicts = []
        for idx, it in enumerate(entries):
            hk = norm_hotkey(it.get("hotkey") or "")
            if not hk: continue
            if hk in mapping:
                conflicts.append(hk); continue
            mapping[to_pynput_combo(hk)] = (lambda idx=idx: play_callback(idx))
        if conflicts and conflict_cb:
            conflict_cb(sorted(set(conflicts)))
        if not mapping:
            return
        try:
            self.listener = GlobalHotKeys(mapping)
            self.listener.start()
        except Exception as e:
            self.listener = None
            if error_cb: error_cb(e)

    def stop(self):
        if self.listener is not None:
            try: self.listener.stop()
            except: pass
            self.listener = None
