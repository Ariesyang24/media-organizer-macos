import threading
from collections import Counter
from pathlib import Path

from scene_engine import SceneRecognizer

namespace = {}
source = Path(__file__).with_name('folder_view_app.pyw').read_text(encoding='utf-8').rsplit('FolderViewApp().mainloop()', 1)[0]
exec(compile(source, 'folder_view_app.pyw', 'exec'), namespace)
FolderViewApp = namespace['FolderViewApp']


class SceneFolderApp(FolderViewApp):
    def __init__(self):
        super().__init__()
        self.scene_on = tk.BooleanVar(value=True)
        self.scene_mode = None
        self._add_scene_controls()

    def _add_scene_controls(self):
        anchor = next((w for w in self.preview.winfo_children() if isinstance(w, ttk.LabelFrame) and str(w.cget('text')) == '素材文件夹'), None)
        controls = ttk.Frame(self.preview, padding=(10, 0, 10, 3))
        if anchor is not None:
            controls.pack(fill='x', after=anchor)
        else:
            controls.pack(fill='x')
        ttk.Checkbutton(controls, text='离线内容场景识别', variable=self.scene_on).pack(side='left')
        ttk.Label(controls, text='照片直接识别，视频通过关键帧识别', foreground='#666').pack(side='left', padx=12)
        self.scene_panel = ttk.LabelFrame(self.preview, text='内容场景文件夹', padding=8)
        self.scene_panel.pack(fill='x', padx=8, pady=(0, 5), after=controls)
        ttk.Label(self.scene_panel, text='扫描后会在这里生成可点击的场景文件夹', foreground='#666').pack(anchor='w')

    def scan(self):
        super().scan()
        if self.stop.is_set() or not self.scene_on.get():
            return
        try:
            recognizer = SceneRecognizer()
            total = len(self.rows)
            for index, row in enumerate(self.rows, 1):
                if self.stop.is_set():
                    break
                if row.get('faces'):
                    result = {'group': '人物', 'label': 'person', 'confidence': 1.0}
                elif row.get('kind') == '视频':
                    result = recognizer.classify_video(row)
                else:
                    result = recognizer.classify_image(row['p'])
                row['scene'] = result
                self.update(index, total, f'内容场景识别 {index}/{total}：{row["p"].name}')
            self.after(0, self.render)
            self.update(total, total, f'场景识别完成：{total} 个素材')
        except Exception as exc:
            # Exception variables are cleared when the except block exits.
            # Capture the message now so the Tk callback always has a value.
            message = str(exc)
            self.after(0, lambda detail=message: self.status.set(f'场景识别未完成：{detail}'))

    def render(self):
        super().render()
        if hasattr(self, 'scene_panel'):
            self._render_scene_folders()

    def _render_scene_folders(self):
        for child in self.scene_panel.winfo_children():
            child.destroy()
        counts = Counter(row.get('scene', {}).get('group') for row in self.rows)
        counts.pop(None, None)
        if not counts:
            ttk.Label(self.scene_panel, text='暂无场景识别结果', foreground='#666').pack(anchor='w')
            return
        for group, count in counts.most_common():
            ttk.Button(
                self.scene_panel,
                text=f'📁  {group}\n{count} 个素材',
                command=lambda value=group: self.open_scene(value)
            ).pack(side='left', fill='x', expand=True, padx=3, ipady=6)

    def open_category(self, category):
        self.scene_mode = None
        super().open_category(category)

    def open_scene(self, scene):
        self.scene_mode = scene
        self.filter_var.set('全部')
        self.search_var.set('')
        self.apply_filter()
        shown = len(self.tree.get_children())
        self.status.set(f'已进入“{scene}”场景文件夹，共 {shown} 个素材')

    def match(self, row):
        if self.scene_mode:
            return row.get('scene', {}).get('group') == self.scene_mode
        return super().match(row)


SceneFolderApp().mainloop()
