import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
from folder_path_overrides import load_path_overrides

launcher = root / 'launch_media_organizer_safe_drag_v10.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV10MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV10MediaOrganizerApp = scope['SafeDragV10MediaOrganizerApp']


class SafeDragV13MediaOrganizerApp(SafeDragV10MediaOrganizerApp):
    INDOOR_SCENES = {'室内其他', '家居室内', '办公学习', '商业购物', '餐饮美食', '舞台娱乐'}
    OUTDOOR_SCENES = {'自然风景', '建筑地标', '街景交通', '运动活'}

    def __init__(self):
        super().__init__()
        self.organize_people = tk.BooleanVar(self, value=False)
        self.organize_scenes = tk.BooleanVar(self, value=False)
        ttk.Separator(self.output_bar, orient='vertical').pack(side='left', fill='y', padx=8)
        self.people_folder_toggle = ttk.Checkbutton(
            self.output_bar, text='按人物子目录', variable=self.organize_people, command=self.toggle_smart_folders)
        self.people_folder_toggle.pack(side='left')
        self.scene_folder_toggle = ttk.Checkbutton(
            self.output_bar, text='按场景子目录', variable=self.organize_scenes, command=self.toggle_smart_folders)
        self.scene_folder_toggle.pack(side='left', padx=(6, 0))

    def _person_folder(self, row):
        people = sorted(str(name).strip() for name in row.get('people', set()) if str(name).strip())
        if not people:
            text = str(row.get('people_text', '')).strip()
            if text and text != '无人脸':
                people = [part.strip() for part in text.replace('、', '|').split('|') if part.strip()]
        if not people:
            return None
        return self.comp(people[0] if len(people) == 1 else '多人_' + '+'.join(people))

    def _scene_folder(self, row):
        group = str(row.get('scene', {}).get('group', '')).strip()
        if group in self.INDOOR_SCENES: return '室内场景'
        if group in self.OUTDOOR_SCENES: return '室外场景'
        return '其他场景'

    def calculate(self):
        super().calculate()
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
            if use_people and person:
                row['target'] = str(base / '人物' / person)
            elif use_scenes:
                row['target'] = str(base / '场景' / self._scene_folder(row))

    def toggle_smart_folders(self):
        self.render()
        choices = []
        if self.organize_people.get(): choices.append('人物')
        if self.organize_scenes.get(): choices.append('场景')
        label = '、'.join(choices) if choices else '均不使用'
        self.status.set(f'智能子目录：{label}；人物和场景同时开启时人物优先')


SafeDragV13MediaOrganizerApp().mainloop()
