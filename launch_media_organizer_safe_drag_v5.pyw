import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_safe_drag_v4.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV4MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV4MediaOrganizerApp = scope['SafeDragV4MediaOrganizerApp']


class SafeDragV5MediaOrganizerApp(SafeDragV4MediaOrganizerApp):
    def render(self):
        # get_children() omits detached rows. Delete both visible and detached
        # items before the inherited renderer reuses numeric item IDs.
        known = set(getattr(self, '_known_tree_iids', set()))
        known.update(str(index) for index in range(len(self.rows)))
        existing = [iid for iid in known if self.tree.exists(iid)]
        if existing:
            self.tree.delete(*existing)
        super().render()
        self._known_tree_iids = {str(index) for index in range(len(self.rows))}


SafeDragV5MediaOrganizerApp().mainloop()
