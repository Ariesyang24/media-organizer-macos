import tkinter as tk
from tkinter import messagebox, ttk

from manager_thumbnail_column import ManagerThumbnailColumn
from material_folder_manager import MaterialFolderManager
from person_group_manager import PersonGroupManager


def _move_action_bar_above_tree(tree):
    parent = tree.master
    frames = [child for child in parent.winfo_children() if child.winfo_class() == 'TFrame']
    for frame in frames:
        try:
            labels = [str(child.cget('text')) for child in frame.winfo_children() if child.winfo_class() == 'TButton']
        except Exception:
            labels = []
        if labels:
            frame.pack_forget()
            frame.pack(fill='x', pady=(0, 8), before=tree)
            return frame
    return None


class PersonGroupManagerV2(PersonGroupManager):
    def __init__(self, app):
        super().__init__(app)
        self.title('模特分类管理 · 缩略图与人工调整')
        self.geometry('1180x760')
        action_bar = _move_action_bar_above_tree(self.files)
        self.move_target = tk.StringVar()
        if action_bar is not None:
            ttk.Label(action_bar, text='移动到：').pack(side='left', padx=(18, 4))
            self.move_box = ttk.Combobox(action_bar, textvariable=self.move_target, state='readonly', width=15)
            self.move_box.pack(side='left')
            ttk.Button(action_bar, text='移动所选素材', command=self.move_files).pack(side='left', padx=5)
        self.thumbnails = ManagerThumbnailColumn(self, self.files, self.app.rows)
        self.refresh()

    def refresh(self, select_name=None):
        super().refresh(select_name)
        names = self.group_names()
        if hasattr(self, 'move_box'):
            self.move_box.configure(values=names)
            if names and self.move_target.get() not in names: self.move_target.set(names[0])
        if hasattr(self, 'thumbnails'): self.after_idle(self.thumbnails.refresh)

    def refresh_files(self):
        super().refresh_files()
        if hasattr(self, 'thumbnails'): self.after_idle(self.thumbnails.refresh)

    def move_files(self):
        source = self.require_one_group(); target = self.move_target.get().strip()
        selected = self.files.selection()
        if not source or not target: return
        if not selected:
            messagebox.showinfo('未选择素材', '请在右侧选择要移动的素材。', parent=self); return
        if source == target:
            messagebox.showinfo('分类相同', '目标模特分类与当前分类相同。', parent=self); return
        for iid in selected:
            row = self.app.rows[int(iid)]; people = row.setdefault('people', set())
            people.discard(source); people.add(target); self.mark(row)
        self.finish_change(target)


class MaterialFolderManagerV2(MaterialFolderManager):
    def __init__(self, app):
        super().__init__(app)
        self.title('素材文件夹管理 · 缩略图与移动调整')
        self.geometry('1180x760')
        action_bar = _move_action_bar_above_tree(self.files)
        self.move_target = tk.StringVar()
        if action_bar is not None:
            ttk.Label(action_bar, text='移动到：').pack(side='left', padx=(18, 4))
            self.move_box = ttk.Combobox(action_bar, textvariable=self.move_target, state='readonly', width=18)
            self.move_box.pack(side='left')
            ttk.Button(action_bar, text='移动所选素材', command=self.move_files).pack(side='left', padx=5)
        self.thumbnails = ManagerThumbnailColumn(self, self.files, self.app.rows)
        self.refresh()

    def refresh(self, select_name=None):
        super().refresh(select_name)
        names = self.folder_names()
        if hasattr(self, 'move_box'):
            self.move_box.configure(values=names)
            if names and self.move_target.get() not in names: self.move_target.set(names[0])
        if hasattr(self, 'thumbnails'): self.after_idle(self.thumbnails.refresh)

    def refresh_files(self):
        super().refresh_files()
        if hasattr(self, 'thumbnails'): self.after_idle(self.thumbnails.refresh)

    def move_files(self):
        target = self.move_target.get().strip(); selected = self.files.selection()
        if not target:
            messagebox.showinfo('请选择目标文件夹', '请先选择要移动到的文件夹。', parent=self); return
        if not selected:
            messagebox.showinfo('未选择素材', '请在右侧选择要移动的素材。', parent=self); return
        for iid in selected: self.assign(self.app.rows[int(iid)], target)
        self.finish(target)
