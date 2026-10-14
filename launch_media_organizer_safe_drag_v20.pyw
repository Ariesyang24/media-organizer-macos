import builtins
import sys
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_safe_drag_v19.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV19MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV19MediaOrganizerApp = scope['SafeDragV19MediaOrganizerApp']


class SafeDragV20MediaOrganizerApp(SafeDragV19MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.faces_on.set(False)
        self.scene_on.set(False)
        self.organize_people.set(False)
        self.organize_scenes.set(False)
        self._move_classification_controls_below_scene_recognition()

    def _move_classification_controls_below_scene_recognition(self):
        # Remove the old copies from the save-location row.
        self.people_folder_toggle.pack_forget()
        self.scene_folder_toggle.pack_forget()
        for child in self.output_bar.winfo_children():
            if child.winfo_class() == 'TSeparator':
                child.pack_forget()

        scene_toggle = None
        old_manager = None
        for widget in self._descendants(self.preview):
            try:
                text = str(widget.cget('text'))
            except Exception:
                continue
            if text == '离线内容场景识别':
                scene_toggle = widget
            elif text == '模特分类管理':
                old_manager = widget
        if old_manager is not None:
            old_manager.pack_forget()
        if scene_toggle is None:
            return

        scene_controls = scene_toggle.master
        self.review_classification_row = ttk.Frame(self.preview, padding=(40, 0, 8, 4))
        self.review_classification_row.pack(fill='x', after=scene_controls)
        ttk.Label(self.review_classification_row, text='整理分类：').pack(side='left')
        self.review_people_folder_toggle = ttk.Checkbutton(
            self.review_classification_row,
            text='按模特分类',
            variable=self.organize_people,
            command=self.toggle_smart_folders,
        )
        self.review_people_folder_toggle.pack(side='left')
        self.review_scene_folder_toggle = ttk.Checkbutton(
            self.review_classification_row,
            text='按场景分类',
            variable=self.organize_scenes,
            command=self.toggle_smart_folders,
        )
        self.review_scene_folder_toggle.pack(side='left', padx=(12, 0))
        ttk.Button(
            self.review_classification_row,
            text='模特分类管理',
            command=self.open_people_manager,
        ).pack(side='left', padx=(12, 0))
        ttk.Label(
            self.review_classification_row,
            text='默认不勾选',
            foreground='#666',
        ).pack(side='left', padx=(12, 0))


SafeDragV20MediaOrganizerApp().mainloop()
