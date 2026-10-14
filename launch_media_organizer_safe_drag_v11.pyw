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


class SafeDragV11MediaOrganizerApp(SafeDragV10MediaOrganizerApp):
    INDOOR_SCENES = {'室内其他', '家居室内', '办公学习', '商业购物', '餐饮美食', '舞台娱乐'}
    OUTDOOR_SCENES = {'自然风景', '建筑地标', '街景交通', '运动活动'}

    def __init__(self):
        self.people_scene_folders = tk.BooleanVar(value=False)
        super().__init__()
        ttk.Separator(self.output_bar, orient='vertical').pack(side='left', fill='y', padx=8)
        self.people_scene_toggle = ttk.Checkbutton(
            self.output_bar,
            text='按人物/场景子目录整理',
            variable=self.people_scene_folders,
            command=self.toggle_people_scene_folders,
        )
        self.people_scene_toggle.pack(side='left')

    def _person_folder(self, row):
        people = sorted(str(name).strip() for name in row.get('people', set()) if str(name).strip())
        if not people:
            text = str(row.get('people_text', '')).strip()
            if text and text != '无人脸':
                people = [part.strip() for part in text.replace('、', '|').split('|') if part.strip()]
        if not people:
            return None
        if len(people) == 1:
            return self.comp(people[0])
        return self.comp('多人_' + '+'.join(people))

    def _scene_folder(self, row):
        group = str(row.get('scene', {}).get('group', '')).strip()
        if group in self.INDOOR_SCENES:
            return '室内场景'
        if group in self.OUTDOOR_SCENES:
            return '室外场景'
        return '其他场景'

    def calculate(self):
        super().calculate()
        if not self.people_scene_folders.get():
            return
        manual_paths = load_path_overrides()
        for row in self.rows:
            if row.get('custom_folder') or str(row.get('p', '')) in manual_paths:
                continue
            person = self._person_folder(row)
            base = Path(row['target'])
            if person:
                row['target'] = str(base / '人物' / person)
            else:
                row['target'] = str(base / '场景' / self._scene_folder(row))

    def toggle_people_scene_folders(self):
        self.render()
        state = '已开启' if self.people_scene_folders.get() else '已关闭'
        self.status.set(f'按人物/场景子目录整理{state}；有人物时人物优先')


SafeDragV11MediaOrganizerApp().mainloop()
