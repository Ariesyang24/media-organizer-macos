import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_safe_drag_v25.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV25MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV25MediaOrganizerApp = scope['SafeDragV25MediaOrganizerApp']


class SafeDragV26MediaOrganizerApp(SafeDragV25MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self._put_people_recognition_first()

    def _put_people_recognition_first(self):
        people = self._find_text_widget(self.preview, '模特识别并分类', 'TCheckbutton')
        quality = self._find_text_widget(self.preview, '画质/重复/连拍识别', 'TCheckbutton')
        if people is None or quality is None or people.master != quality.master:
            return
        manager = getattr(self, 'review_people_manager', None)
        people.pack_forget()
        quality.pack_forget()
        if manager is not None:
            manager.pack_forget()
        people.pack(side='left')
        quality.pack(side='left', padx=(12, 0))
        if manager is not None:
            manager.pack(side='left', padx=(8, 0))


class SafeDragV27MediaOrganizerApp(SafeDragV26MediaOrganizerApp):
    pass


SafeDragV27MediaOrganizerApp().mainloop()
