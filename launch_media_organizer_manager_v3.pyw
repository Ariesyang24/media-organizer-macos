import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

from manager_ui_v3 import MaterialFolderManagerV3, PersonGroupManagerV3
from material_folder_manager import apply_saved_material_folders

launcher = root / 'launch_media_organizer_manager_v2.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('ManagerV2MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
ManagerV2MediaOrganizerApp = scope['ManagerV2MediaOrganizerApp']


class ManagerV3MediaOrganizerApp(ManagerV2MediaOrganizerApp):
    def open_people_manager(self):
        PersonGroupManagerV3(self)

    def open_material_folders(self):
        apply_saved_material_folders(self.rows)
        MaterialFolderManagerV3(self)


ManagerV3MediaOrganizerApp().mainloop()
