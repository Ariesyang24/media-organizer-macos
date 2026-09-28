from pathlib import Path

namespace = {}
source = Path(__file__).with_name('launch_scene_folder_final.pyw').read_text(encoding='utf-8').rsplit('FinalSceneFolderApp().mainloop()', 1)[0]
exec(compile(source, 'launch_scene_folder_final.pyw', 'exec'), namespace)
FinalSceneFolderApp = namespace['FinalSceneFolderApp']


class AIEntryApp(FinalSceneFolderApp):
    def __init__(self):
        super().__init__()
        self.ai_mode = tk.StringVar(value='本地AI')
        self._add_ai_entry()
        self._add_ai_result_column()

    def _add_ai_entry(self):
        header = self.winfo_children()[0]
        ttk.Button(header, text='✨ AI识别', command=self.open_ai_settings).pack(side='right', padx=(0, 8), before=self.action)

    def _add_ai_result_column(self):
        columns = tuple(self.tree['columns'])
        if 'ai_scene' not in columns:
            self.tree.configure(columns=columns + ('ai_scene',))
            self.tree.heading('ai_scene', text='AI内容')
            self.tree.column('ai_scene', width=150, anchor='w')

    def open_ai_settings(self):
        window = tk.Toplevel(self)
        window.title('AI识别设置')
        window.geometry('560x410')
        window.resizable(False, False)
        window.transient(self)
        window.grab_set()

        shell = ttk.Frame(window, padding=22)
        shell.pack(fill='both', expand=True)
        ttk.Label(shell, text='AI识别', font=('Segoe UI', 17, 'bold')).pack(anchor='w')
        ttk.Label(shell, text='选择素材识别方式', foreground='#666').pack(anchor='w', pady=(3, 16))

        local = ttk.LabelFrame(shell, text='本地AI（推荐）', padding=12)
        local.pack(fill='x')
        ttk.Radiobutton(local, text='启用本地AI识别', variable=self.ai_mode, value='本地AI', command=self._apply_ai_mode).pack(anchor='w')
        ttk.Label(local, text='素材不上传。识别人物、家居、商业、街景、自然、餐饮、舞台等内容。', foreground='#555', wraplength=480).pack(anchor='w', pady=(5, 0))

        cloud = ttk.LabelFrame(shell, text='云端AI', padding=12)
        cloud.pack(fill='x', pady=12)
        ttk.Radiobutton(cloud, text='使用云端AI（需配置服务）', variable=self.ai_mode, value='云端AI', command=self._apply_ai_mode).pack(anchor='w')
        ttk.Label(cloud, text='可用于更详细的画面描述、物体和活动识别。在未配置前不会上传任何素材。', foreground='#777', wraplength=480).pack(anchor='w', pady=(5, 0))
        ttk.Button(cloud, text='配置云端AI…', command=self.cloud_placeholder).pack(anchor='w', pady=(9, 0))

        state = '已启用' if self.scene_on.get() else '已关闭'
        self.ai_state_label = ttk.Label(shell, text=f'当前：{self.ai_mode.get()} · {state}', foreground='#1267a5')
        self.ai_state_label.pack(anchor='w', pady=(5, 0))
        ttk.Button(shell, text='完成', command=window.destroy).pack(side='right', pady=(14, 0))

    def _apply_ai_mode(self):
        if self.ai_mode.get() == '本地AI':
            self.scene_on.set(True)
            text = '当前：本地AI · 已启用'
        else:
            self.scene_on.set(False)
            text = '当前：云端AI · 等待配置'
        if hasattr(self, 'ai_state_label'):
            self.ai_state_label.configure(text=text)

    def cloud_placeholder(self):
        messagebox.showinfo(
            '云端AI配置',
            '云端AI入口已保留。\n\n请先确定要使用的AI服务，再配置密钥。\n未配置前不会上传任何素材。',
            parent=self
        )

    def render(self):
        super().render()
        if not hasattr(self, 'tree') or 'ai_scene' not in self.tree['columns']:
            return
        for index, row in enumerate(self.rows):
            item = str(index)
            if self.tree.exists(item):
                scene = row.get('scene', {})
                text = scene.get('group', '')
                if scene.get('label'):
                    text += f' / {scene["label"]}'
                self.tree.set(item, 'ai_scene', text)


AIEntryApp().mainloop()
