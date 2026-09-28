import builtins
import sys
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))

import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES
from scene_engine import SceneRecognizer, SCENE_RULES

SCENE_RULES['家居室内'] += ('bedchamber', 'dressing_room')
SCENE_RULES['街景交通'] += ('cockpit', 'airplane_cabin', 'medina')

builtins.tk = tk
builtins.ttk = ttk
builtins.__file__ = str(root / 'batch3_media_organizer.pyw')

clean_path = root / 'clean_ui_app.pyw'
clean_source = clean_path.read_text(encoding='utf-8').rsplit('CleanUIApp().mainloop()', 1)[0]
clean_scope = {'tk': tk, 'ttk': ttk, '__file__': str(clean_path)}
exec(compile(clean_source, str(clean_path), 'exec'), clean_scope)
clean_scope['CleanUIApp']._rebuild_setup.__globals__['namespace']['DND_FILES'] = DND_FILES

folder_path = root / 'folder_view_app.pyw'
folder_source = folder_path.read_text(encoding='utf-8').rsplit('FolderViewApp().mainloop()', 1)[0]
folder_scope = {'tk': tk, 'ttk': ttk, '__file__': str(folder_path), 'Path': Path, 'CleanUIApp': clean_scope['CleanUIApp']}
exec(compile(folder_source[folder_source.index('class FolderViewApp'):], str(folder_path), 'exec'), folder_scope)

scene_path = root / 'scene_folder_app.pyw'
scene_source = scene_path.read_text(encoding='utf-8').rsplit('SceneFolderApp().mainloop()', 1)[0]
scene_scope = {
    'tk': tk, 'ttk': ttk, '__file__': str(scene_path), 'Path': Path,
    'Counter': Counter, 'SceneRecognizer': SceneRecognizer,
    'FolderViewApp': folder_scope['FolderViewApp']
}
exec(compile(scene_source[scene_source.index('class SceneFolderApp'):], str(scene_path), 'exec'), scene_scope)


class FinalSceneFolderApp(scene_scope['SceneFolderApp']):
    def _render_scene_folders(self):
        for child in self.scene_panel.winfo_children():
            child.destroy()
        counts = Counter(row.get('scene', {}).get('group') for row in self.rows)
        counts.pop(None, None)
        if not counts:
            ttk.Label(self.scene_panel, text='暂无场景识别结果', foreground='#666').grid(row=0, column=0, sticky='w')
            return
        for column in range(5):
            self.scene_panel.columnconfigure(column, weight=1)
        for index, (group, count) in enumerate(counts.most_common()):
            ttk.Button(
                self.scene_panel,
                text=f'📁  {group}\n{count} 个素材',
                command=lambda value=group: self.open_scene(value)
            ).grid(row=index // 5, column=index % 5, sticky='nsew', padx=3, pady=3, ipady=5)


FinalSceneFolderApp().mainloop()
