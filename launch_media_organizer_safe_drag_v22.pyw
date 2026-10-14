import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_safe_drag_v21.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV21MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV21MediaOrganizerApp = scope['SafeDragV21MediaOrganizerApp']


class SafeDragV22MediaOrganizerApp(SafeDragV21MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self._connect_classification_dependencies()
        self._remove_default_off_hint()

    def _connect_classification_dependencies(self):
        for container in (self.setup_classification, self.review_classification_row):
            for widget in container.winfo_children():
                if widget.winfo_class() != 'TCheckbutton':
                    continue
                text = str(widget.cget('text'))
                if text == '按模特分类':
                    widget.configure(command=self._people_classification_changed)
                elif text == '按场景分类':
                    widget.configure(command=self._scene_classification_changed)

    def _people_classification_changed(self):
        if self.organize_people.get():
            self.faces_on.set(True)
        self.toggle_smart_folders()

    def _scene_classification_changed(self):
        if self.organize_scenes.get():
            self.scene_on.set(True)
            if hasattr(self, 'update_scene_visibility'):
                self.update_scene_visibility()
        self.toggle_smart_folders()

    def _remove_default_off_hint(self):
        for widget in list(self.review_classification_row.winfo_children()):
            try:
                if widget.winfo_class() == 'TLabel' and str(widget.cget('text')) == '默认不勾选':
                    widget.destroy()
            except Exception:
                pass


SafeDragV22MediaOrganizerApp().mainloop()
