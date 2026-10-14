import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_safe_drag_v24.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV24MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV24MediaOrganizerApp = scope['SafeDragV24MediaOrganizerApp']


class SafeDragV25MediaOrganizerApp(SafeDragV24MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self._merge_recognition_and_classification_switches()

    def _merge_recognition_and_classification_switches(self):
        # Remove legacy hidden switches so a later layout refresh cannot show duplicates.
        for legacy_name in ('people_folder_toggle', 'scene_folder_toggle'):
            legacy = getattr(self, legacy_name, None)
            if legacy is not None:
                legacy.destroy()
        scene = self._find_text_widget(self.preview, '离线内容场景识别', 'TCheckbutton')
        people = self._find_text_widget(self.preview, '离线人脸与人物聚类', 'TCheckbutton')
        if scene is not None:
            scene.configure(text='场景识别并分类', command=self._scene_combined_changed)
        if people is not None:
            people.configure(text='模特识别并分类', command=self._people_combined_changed)

        if hasattr(self, 'review_scene_folder_toggle'):
            self.review_scene_folder_toggle.destroy()
        if hasattr(self, 'review_people_folder_toggle'):
            self.review_people_folder_toggle.destroy()

        for widget in self.setup_classification.winfo_children():
            if widget.winfo_class() != 'TCheckbutton':
                continue
            text = str(widget.cget('text'))
            if text == '按场景分类':
                widget.configure(text='场景识别并分类', variable=self.scene_on, command=self._scene_combined_changed)
            elif text == '按模特分类':
                widget.configure(text='模特识别并分类', variable=self.faces_on, command=self._people_combined_changed)

    def _scene_combined_changed(self):
        self.organize_scenes.set(bool(self.scene_on.get()))
        if hasattr(self, 'update_scene_visibility'):
            self.update_scene_visibility()
        if self.rows:
            self.render()

    def _people_combined_changed(self):
        self.organize_people.set(bool(self.faces_on.get()))
        if self.rows:
            self.render()


SafeDragV25MediaOrganizerApp().mainloop()
