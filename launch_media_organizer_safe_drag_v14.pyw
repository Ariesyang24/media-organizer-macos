import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
from folder_path_overrides import load_path_overrides

launcher = root / 'launch_media_organizer_safe_drag_v13.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV13MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV13MediaOrganizerApp = scope['SafeDragV13MediaOrganizerApp']


class SafeDragV14MediaOrganizerApp(SafeDragV13MediaOrganizerApp):
    def _scene_folder(self, row):
        group = str(row.get('scene', {}).get('group', '')).strip()
        if group in self.INDOOR_SCENES: return '室内场景'
        if group in self.OUTDOOR_SCENES: return '室外场景'
        return None

    def calculate(self):
        # Call the pre-smart-folder calculation so every toggle starts from
        # the original date/place/device/type layout.
        super(SafeDragV13MediaOrganizerApp, self).calculate()
        people_option = getattr(self, 'organize_people', None)
        scene_option = getattr(self, 'organize_scenes', None)
        use_people = bool(people_option and people_option.get())
        use_scenes = bool(scene_option and scene_option.get())
        if not use_people and not use_scenes: return
        manual_paths = load_path_overrides()
        for row in self.rows:
            if row.get('custom_folder') or str(row.get('p', '')) in manual_paths: continue
            base = Path(row['target'])
            person = self._person_folder(row)
            scene = self._scene_folder(row)
            if use_people and person:
                row['target'] = str(base / '人物' / person)
            elif use_scenes and scene:
                row['target'] = str(base / '场景' / scene)


SafeDragV14MediaOrganizerApp().mainloop()
