import builtins, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scene-runtime'))
builtins.__file__ = str(ROOT / 'launch_scene_folder_final.pyw')
launcher = ROOT / 'launch_media_organizer_safe_drag_v38.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV38MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV38MediaOrganizerApp = scope['SafeDragV38MediaOrganizerApp']

from state_actions_v42 import StateActionsV42
from recognition_page_state_v40 import WAITING, SCANNING, PAUSED, COMPLETED, FAILED


class SafeDragV42MediaOrganizerApp(SafeDragV38MediaOrganizerApp):
    def __init__(self):
        self.page_state = None
        super().__init__()
        self.minsize(1100, 680)
        self.page_state = StateActionsV42(self)

    def render(self):
        super().render()
        if self.page_state is not None and not self.scan_busy:
            self.page_state.apply(COMPLETED if self.rows else WAITING)

    def _refresh_scan_availability(self):
        super()._refresh_scan_availability()
        if self.page_state is not None and self.page_state.value.get() == WAITING:
            self.page_state.apply(WAITING)

    def start_scan(self):
        if self._validation_error():
            return super().start_scan()
        result = super().start_scan()
        self.page_state.apply(SCANNING)
        return result

    def toggle_pause(self):
        super().toggle_pause()
        if self.scan_busy:
            self.page_state.apply(PAUSED if self.scan_pause.is_set() else SCANNING)

    def _show_progress(self, number, total, text):
        super()._show_progress(number, total, text)
        if self.page_state is not None and self.scan_busy:
            self.page_state.apply(PAUSED if self.scan_pause.is_set() else SCANNING)

    def _finish_scan(self, error):
        super()._finish_scan(error)
        if error is not None:
            self.page_state.apply(FAILED, error)
        elif self.stop.is_set():
            self.page_state.apply(FAILED, '扫描已停止，已完成的结果已保留')
        else:
            self.page_state.apply(COMPLETED)


if __name__ == '__main__':
    SafeDragV42MediaOrganizerApp().mainloop()
