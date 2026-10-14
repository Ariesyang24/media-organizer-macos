import builtins
import sys
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_safe_drag_v18.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV18MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV18MediaOrganizerApp = scope['SafeDragV18MediaOrganizerApp']


class SafeDragV19MediaOrganizerApp(SafeDragV18MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self._rename_review_classification_options()
        self._add_setup_classification_options()
        self._move_people_manager_next_to_face_option()

    def _rename_review_classification_options(self):
        self.people_folder_toggle.configure(text='按模特分类')
        self.scene_folder_toggle.configure(text='按场景分类')

    def _find_setup_output_panel(self):
        for widget in self.setup.winfo_children():
            for child in self._descendants(widget):
                try:
                    if child.winfo_class() == 'TLabelframe' and str(child.cget('text')).startswith('2  '):
                        return child
                except Exception:
                    pass
        return None

    def _descendants(self, widget):
        for child in widget.winfo_children():
            yield child
            yield from self._descendants(child)

    def _add_setup_classification_options(self):
        panel = self._find_setup_output_panel()
        if panel is None:
            return
        before_widget = None
        for child in panel.winfo_children():
            try:
                if str(child.cget('text')) == '整理后的保存位置':
                    before_widget = child
                    break
            except Exception:
                pass
        self.setup_classification = ttk.LabelFrame(panel, text='分类目录（可选）', padding=(10, 7))
        pack_options = {'fill': 'x', 'pady': (10, 2)}
        if before_widget is not None:
            pack_options['before'] = before_widget
        self.setup_classification.pack(**pack_options)
        ttk.Checkbutton(
            self.setup_classification,
            text='按模特分类',
            variable=self.organize_people,
            command=self.toggle_smart_folders,
        ).pack(side='left')
        ttk.Checkbutton(
            self.setup_classification,
            text='按场景分类',
            variable=self.organize_scenes,
            command=self.toggle_smart_folders,
        ).pack(side='left', padx=(18, 0))
        ttk.Label(
            self.setup_classification,
            text='默认不勾选，可单独或同时启用',
            foreground='#666',
        ).pack(side='left', padx=(18, 0))

    def _move_people_manager_next_to_face_option(self):
        manager = None
        face_option = None
        for widget in self._descendants(self.preview):
            try:
                text = str(widget.cget('text'))
            except Exception:
                continue
            if text == '模特分类管理':
                manager = widget
            elif text == '离线人脸与人物聚类':
                face_option = widget
        if manager is None or face_option is None or manager.master != face_option.master:
            return
        manager.pack_forget()
        manager.pack(side='left', padx=(8, 0), after=face_option)


SafeDragV19MediaOrganizerApp().mainloop()
