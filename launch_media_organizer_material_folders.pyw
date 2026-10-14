import builtins
import sys
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

from material_folder_manager import MaterialFolderManager, apply_custom_targets, apply_saved_material_folders

people_path = root / 'launch_media_organizer_people_manager.pyw'
source = people_path.read_text(encoding='utf-8').rsplit('PeopleManagerMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(people_path)}
exec(compile(source, str(people_path), 'exec'), scope)
PeopleManagerMediaOrganizerApp = scope['PeopleManagerMediaOrganizerApp']


class MaterialFolderMediaOrganizerApp(PeopleManagerMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self._add_material_folder_button(self)
        self.status.set('可用“素材文件夹管理”把选中素材放入自己创建的分类目录')

    def _add_material_folder_button(self, widget):
        for child in widget.winfo_children():
            try:
                if child.winfo_class() == 'TButton' and str(child.cget('text')) == '模特分类管理':
                    ttk.Button(child.master, text='素材文件夹管理', command=self.open_material_folders).pack(side='right', padx=6)
                    return True
            except Exception:
                pass
            if self._add_material_folder_button(child):
                return True
        return False

    def open_material_folders(self):
        apply_saved_material_folders(self.rows)
        MaterialFolderManager(self)

    def calculate(self):
        apply_saved_material_folders(self.rows)
        super().calculate()
        apply_custom_targets(self.rows)


MaterialFolderMediaOrganizerApp().mainloop()
