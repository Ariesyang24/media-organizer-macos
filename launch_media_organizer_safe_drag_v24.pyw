import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_safe_drag_v23.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV23MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV23MediaOrganizerApp = scope['SafeDragV23MediaOrganizerApp']


class SafeDragV24MediaOrganizerApp(SafeDragV23MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self._stack_scene_and_people_rows()

    def _stack_scene_and_people_rows(self):
        scene_recognition = self._find_text_widget(self.preview, '离线内容场景识别', 'TCheckbutton')
        face_recognition = self._find_text_widget(self.preview, '离线人脸与人物聚类', 'TCheckbutton')
        if scene_recognition is None or face_recognition is None:
            return
        scene_row = scene_recognition.master
        people_row = face_recognition.master
        if scene_row.master != people_row.master:
            return
        people_row.pack_forget()
        people_row.pack(fill='x', padx=10, pady=3, after=scene_row)


SafeDragV24MediaOrganizerApp().mainloop()
