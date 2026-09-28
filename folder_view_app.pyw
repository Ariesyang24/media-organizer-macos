from pathlib import Path

namespace = {}
source = Path(__file__).with_name('clean_ui_app.pyw').read_text(encoding='utf-8').rsplit('CleanUIApp().mainloop()', 1)[0]
exec(compile(source, 'clean_ui_app.pyw', 'exec'), namespace)
CleanUIApp = namespace['CleanUIApp']


class FolderViewApp(CleanUIApp):
    def __init__(self):
        super().__init__()
        self._build_folder_navigation()
        self.status.set('添加素材文件夹，扫描后点击分类文件夹查看')

    def _build_folder_navigation(self):
        old_progress = self.progress
        old_progress.pack_forget()
        old_progress.destroy()

        children = self.preview.winfo_children()
        old_cards = children[0] if children else None
        if old_cards is not None:
            old_cards.destroy()

        first = self.preview.winfo_children()[0] if self.preview.winfo_children() else None
        progress_panel = ttk.Frame(self.preview, padding=(8, 8, 8, 2))
        if first is not None:
            progress_panel.pack(fill='x', before=first)
        else:
            progress_panel.pack(fill='x')
        ttk.Label(progress_panel, text='识别进度').pack(side='left', padx=(0, 10))
        self.progress = ttk.Progressbar(progress_panel)
        self.progress.pack(side='left', fill='x', expand=True)

        folder_panel = ttk.LabelFrame(self.preview, text='素材文件夹', padding=8)
        folder_panel.pack(fill='x', padx=8, pady=(3, 5), after=progress_panel)
        self.folder_labels = [tk.StringVar() for _ in range(4)]
        names = ('全部', '照片', '视频', '失败/跳过')
        for index, name in enumerate(names):
            button = ttk.Button(
                folder_panel,
                textvariable=self.folder_labels[index],
                command=lambda value=name: self.open_category(value)
            )
            button.pack(side='left', fill='x', expand=True, padx=4, ipady=9)
        self._sync_folder_labels()

    def _sync_folder_labels(self):
        if not hasattr(self, 'folder_labels'):
            return
        photos = sum(row.get('kind') == '照片' for row in self.rows)
        videos = sum(row.get('kind') == '视频' for row in self.rows)
        failed = sum(
            not row.get('analysis', {}).get('valid', True)
            or row.get('recommend') == '无法解码'
            for row in self.rows
        )
        counts = (len(self.rows), photos, videos, failed)
        names = ('全部', '照片', '视频', '失败/跳过')
        for variable, count, name in zip(self.folder_labels, counts, names):
            variable.set(f'📁  {name}\n{count} 个素材')

    def open_category(self, category):
        self.filter_var.set(category)
        self.search_var.set('')
        self.apply_filter()
        shown = len(self.tree.get_children())
        self.status.set(f'已进入“{category}”文件夹，共 {shown} 个素材')

    def match(self, row):
        mode = self.filter_var.get()
        if mode == '照片':
            category_match = row.get('kind') == '照片'
        elif mode == '视频':
            category_match = row.get('kind') == '视频'
        elif mode == '失败/跳过':
            category_match = (
                not row.get('analysis', {}).get('valid', True)
                or row.get('recommend') == '无法解码'
            )
        else:
            return super().match(row)
        text = self.search_var.get().strip().lower()
        haystack = ' '.join([
            row['p'].name,
            row.get('dev', ''),
            row.get('place', ''),
            row.get('people_text', ''),
            row.get('recommend', '')
        ]).lower()
        return category_match and (not text or text in haystack)

    def render(self):
        super().render()
        self._sync_folder_labels()


FolderViewApp().mainloop()
