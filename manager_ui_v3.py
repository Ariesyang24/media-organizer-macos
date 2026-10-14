from tkinter import messagebox, ttk

from manager_ui_v2 import MaterialFolderManagerV2, PersonGroupManagerV2


class PersonGroupManagerV3(PersonGroupManagerV2):
    def __init__(self, app):
        super().__init__(app)
        bar = ttk.Frame(self.files.master)
        bar.pack(fill='x', pady=(0, 8), before=self.files)
        ttk.Label(bar, text='批量选择：').pack(side='left')
        ttk.Button(bar, text='全选右侧', command=self.select_all_files).pack(side='left', padx=4)
        ttk.Button(bar, text='取消全选', command=lambda: self.files.selection_remove(*self.files.selection())).pack(side='left')
        ttk.Button(bar, text='批量移出当前模特组', command=self.remove_files).pack(side='left', padx=12)

    def select_all_files(self):
        children = self.files.get_children('')
        if children: self.files.selection_set(children)


class MaterialFolderManagerV3(MaterialFolderManagerV2):
    def __init__(self, app):
        self.showing_unassigned = False
        super().__init__(app)
        bar = ttk.Frame(self.files.master)
        bar.pack(fill='x', pady=(0, 8), before=self.files)
        ttk.Button(bar, text='查看当前文件夹', command=self.show_current_folder).pack(side='left')
        ttk.Button(bar, text='查看未分类素材', command=self.show_unassigned).pack(side='left', padx=5)
        ttk.Separator(bar, orient='vertical').pack(side='left', fill='y', padx=8)
        ttk.Button(bar, text='全选右侧', command=self.select_all_files).pack(side='left')
        ttk.Button(bar, text='取消全选', command=lambda: self.files.selection_remove(*self.files.selection())).pack(side='left', padx=5)
        ttk.Button(bar, text='批量选入当前文件夹', command=self.batch_add).pack(side='left', padx=(12, 5))
        ttk.Button(bar, text='批量移出当前文件夹', command=self.batch_remove).pack(side='left')
        self.refresh_files()

    def populate_rows(self, predicate):
        self.files.delete(*self.files.get_children())
        for index, row in enumerate(self.app.rows):
            if predicate(row):
                self.files.insert('', 'end', iid=str(index), values=(row['p'].name, row.get('kind', '')))
        if hasattr(self, 'thumbnails'): self.after_idle(self.thumbnails.refresh)

    def refresh_files(self):
        if getattr(self, 'showing_unassigned', False):
            self.populate_rows(lambda row: not row.get('custom_folder'))
        else:
            super().refresh_files()

    def show_current_folder(self):
        self.showing_unassigned = False
        self.refresh_files()

    def show_unassigned(self):
        self.showing_unassigned = True
        self.populate_rows(lambda row: not row.get('custom_folder'))

    def select_all_files(self):
        children = self.files.get_children('')
        if children: self.files.selection_set(children)

    def batch_add(self):
        folder = self.current_folder()
        if not folder: return
        selected = self.files.selection()
        if not selected:
            messagebox.showinfo('未选择素材', '请先选择素材，或点击“全选右侧”。', parent=self); return
        for iid in selected: self.assign(self.app.rows[int(iid)], folder)
        self.finish(folder)

    def batch_remove(self):
        if self.showing_unassigned:
            messagebox.showinfo('当前是未分类素材', '未分类素材无需移出，请切换到“查看当前文件夹”。', parent=self); return
        folder = self.current_folder()
        if not folder: return
        selected = self.files.selection()
        if not selected:
            messagebox.showinfo('未选择素材', '请先选择素材，或点击“全选右侧”。', parent=self); return
        for iid in selected:
            row = self.app.rows[int(iid)]
            if row.get('custom_folder') == folder: self.assign(row, '')
        self.finish(folder)
