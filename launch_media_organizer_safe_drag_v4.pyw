import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

from folder_path_overrides import load_path_overrides, save_path_overrides
from material_folder_manager import save_material_folders

launcher = root / 'launch_media_organizer_safe_drag_v3.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV3MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV3MediaOrganizerApp = scope['SafeDragV3MediaOrganizerApp']


class SafeDragV4MediaOrganizerApp(SafeDragV3MediaOrganizerApp):
    TARGET_PREFIX = '__TARGET_PATH__:'

    def _sidebar_drop_target(self, index):
        if not (0 <= index < len(self.sidebar_targets)):
            return '__AUTO__', None
        kind, value = self.sidebar_targets[index]
        if kind == 'empty':
            return value, ('custom', value)
        if kind == 'target':
            if '自定义分类' in Path(value).parts:
                name = Path(value).parts[-1]
                return name, ('custom', name)
            return self.TARGET_PREFIX + value, value
        return '__AUTO__', None

    def drop_rows(self, rows, folder):
        if not isinstance(folder, str) or not folder.startswith(self.TARGET_PREFIX):
            return super().drop_rows(rows, folder)
        target = folder[len(self.TARGET_PREFIX):]
        changed = {str(row['p']) for row in rows}
        for row in rows:
            row['custom_folder'] = ''
        save_material_folders(self.rows, changed)
        overrides = load_path_overrides()
        for row in rows:
            overrides[str(row['p'])] = target
        save_path_overrides(overrides)
        self.render()
        self.status.set(f'已将 {len(rows)} 个素材移入目标文件夹：{target}')


SafeDragV4MediaOrganizerApp().mainloop()
