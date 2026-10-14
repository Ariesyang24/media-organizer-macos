import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
from folder_path_overrides import load_path_overrides

launcher = root / 'launch_media_organizer_safe_drag_v14.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV14MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV14MediaOrganizerApp = scope['SafeDragV14MediaOrganizerApp']


class SafeDragV15MediaOrganizerApp(SafeDragV14MediaOrganizerApp):
    def calculate(self):
        super().calculate()
        manual_paths = load_path_overrides()
        for row in self.rows:
            if str(row.get('p', '')) in manual_paths:
                continue
            place = str(row.get('place', '')).strip()
            if place not in {'', '未设置'}:
                continue
            target = Path(row.get('target', ''))
            parts = list(target.parts)
            if not parts:
                continue
            date = str(row.get('date', '')).replace('-', '.')
            if parts[0] in {f'{date} 未设置', f'{date} Unknown', f'{date}'}:
                parts[0] = date
                row['target'] = str(Path(*parts))


SafeDragV15MediaOrganizerApp().mainloop()
