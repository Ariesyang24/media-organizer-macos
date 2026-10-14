import builtins
import sys
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_safe_drag_v22.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV22MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV22MediaOrganizerApp = scope['SafeDragV22MediaOrganizerApp']


class SafeDragV23MediaOrganizerApp(SafeDragV22MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self._merge_classification_with_recognition_rows()

    def _find_text_widget(self, parent, text, widget_class=None):
        for widget in self._descendants(parent):
            try:
                if (widget_class is None or widget.winfo_class() == widget_class) and str(widget.cget('text')) == text:
                    return widget
            except Exception:
                pass
        return None

    def _merge_classification_with_recognition_rows(self):
        if hasattr(self, 'review_classification_row'):
            self.review_classification_row.destroy()

        scene_recognition = self._find_text_widget(self.preview, '离线内容场景识别', 'TCheckbutton')
        face_recognition = self._find_text_widget(self.preview, '离线人脸与人物聚类', 'TCheckbutton')
        if scene_recognition is not None:
            self.review_scene_folder_toggle = ttk.Checkbutton(
                scene_recognition.master,
                text='按场景分类',
                variable=self.organize_scenes,
                command=self._scene_classification_changed,
            )
            self.review_scene_folder_toggle.pack(side='left', padx=(14, 0), after=scene_recognition)

        if face_recognition is not None:
            self.review_people_folder_toggle = ttk.Checkbutton(
                face_recognition.master,
                text='按模特分类',
                variable=self.organize_people,
                command=self._people_classification_changed,
            )
            self.review_people_folder_toggle.pack(side='left', padx=(12, 0), after=face_recognition)
            self.review_people_manager = ttk.Button(
                face_recognition.master,
                text='模特分类管理',
                command=self.open_people_manager,
            )
            self.review_people_manager.pack(side='left', padx=(8, 0), after=self.review_people_folder_toggle)


SafeDragV23MediaOrganizerApp().mainloop()
