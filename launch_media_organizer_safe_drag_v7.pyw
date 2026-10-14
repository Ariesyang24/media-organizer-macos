import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_safe_drag_v5.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV5MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV5MediaOrganizerApp = scope['SafeDragV5MediaOrganizerApp']


class SafeDragV7MediaOrganizerApp(SafeDragV5MediaOrganizerApp):
    """Keep the complete selection when a drag begins on a selected row."""

    def __init__(self):
        super().__init__()
        self._drag_selection_snapshot = ()
        self._drag_pressed_iid = ''
        capture_tag = f'DragSelectionCapture_{id(self.tree)}'
        tags = list(self.tree.bindtags())
        tags.insert(0, capture_tag)
        self.tree.bindtags(tuple(tags))
        self.tree.bind_class(capture_tag, '<ButtonPress-1>', self._capture_drag_selection, add='+')

    def _capture_drag_selection(self, event):
        iid = self.tree.identify_row(event.y)
        selected = tuple(self.tree.selection())
        self._drag_pressed_iid = iid
        self._drag_selection_snapshot = selected if iid and iid in selected else ()
        self.drag_press_point = (event.x_root, event.y_root) if iid else None

    def start_row_drag(self, event):
        if self.drag_press_point is None:
            return
        dx = event.x_root - self.drag_press_point[0]
        dy = event.y_root - self.drag_press_point[1]
        if not self.drag_active and dx * dx + dy * dy < self.DRAG_THRESHOLD * self.DRAG_THRESHOLD:
            return
        valid = tuple(iid for iid in self._drag_selection_snapshot if self.tree.exists(iid))
        if valid and self._drag_pressed_iid in valid:
            self.tree.selection_set(valid)
            self.tree.focus(self._drag_pressed_iid)
            self.update_selection_status()
        super().start_row_drag(event)

    def finish_row_drag(self, event):
        try:
            super().finish_row_drag(event)
        finally:
            self._drag_selection_snapshot = ()
            self._drag_pressed_iid = ''


SafeDragV7MediaOrganizerApp().mainloop()
