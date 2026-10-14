import builtins
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scene-runtime'))
builtins.__file__=str(ROOT/'launch_scene_folder_final.pyw')
launcher=ROOT/'launch_media_organizer_safe_drag_v37.pyw'
source=launcher.read_text(encoding='utf-8').rsplit('SafeDragV37MediaOrganizerApp().mainloop()',1)[0]
scope={'__file__':str(launcher)}
exec(compile(source,str(launcher),'exec'),scope)
SafeDragV37MediaOrganizerApp=scope['SafeDragV37MediaOrganizerApp']

from waiting_state_v38 import WaitingStateV38


class SafeDragV38MediaOrganizerApp(SafeDragV37MediaOrganizerApp):
    """Zero-assets waiting-state layout only; scan and organize logic remain inherited."""
    def __init__(self):
        self.waiting_v38=None
        super().__init__()
        self.waiting_v38=WaitingStateV38(self)
        self.after_idle(self.waiting_v38.refresh)

    def render(self):
        super().render()
        if self.waiting_v38 is not None:self.waiting_v38.refresh()

    def _refresh_scan_availability(self):
        super()._refresh_scan_availability()
        if self.waiting_v38 is not None:self.waiting_v38.refresh()

    def toggle_settings_drawer(self):
        if self.waiting_v38 is not None:self.waiting_v38.open_settings()
        else:super().toggle_settings_drawer()


SafeDragV38MediaOrganizerApp().mainloop()
