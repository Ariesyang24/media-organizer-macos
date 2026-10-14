import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

from manager_ui_v2 import MaterialFolderManagerV2, PersonGroupManagerV2
from material_folder_manager import apply_saved_material_folders

launcher = root / 'launch_media_organizer_material_folders.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('MaterialFolderMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
MaterialFolderMediaOrganizerApp = scope['MaterialFolderMediaOrganizerApp']


class ManagerV2MediaOrganizerApp(MaterialFolderMediaOrganizerApp):
    def open_people_manager(self):
        PersonGroupManagerV2(self)

    def open_material_folders(self):
        apply_saved_material_folders(self.rows)
        MaterialFolderManagerV2(self)

    def calculate(self):
        apply_saved_material_folders(self.rows)
        super(MaterialFolderMediaOrganizerApp, self).calculate()
        for row in self.rows:
            folder = row.get('custom_folder', '').strip()
            if folder:
                row['target'] = str(Path(row['target']) / '自定义分类' / folder)


ManagerV2MediaOrganizerApp().mainloop()
