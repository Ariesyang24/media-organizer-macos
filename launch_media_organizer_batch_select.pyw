import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_inline_folders.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('InlineFolderMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
InlineFolderMediaOrganizerApp = scope['InlineFolderMediaOrganizerApp']


class BatchSelectMediaOrganizerApp(InlineFolderMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.batch_select_mode = tk.BooleanVar(value=False)
        self.selection_text = tk.StringVar(value='已选择 0 个')
        ttk.Separator(self.folder_bar, orient='vertical').pack(side='left', fill='y', padx=8)
        ttk.Checkbutton(
            self.folder_bar,
            text='批量选择模式（点击即可多选）',
            variable=self.batch_select_mode,
            command=self.update_selection_status,
        ).pack(side='left')
        ttk.Button(self.folder_bar, text='全选当前列表', command=self.select_all_visible).pack(side='left', padx=5)
        ttk.Button(self.folder_bar, text='清空选择', command=self.clear_selection).pack(side='left')
        ttk.Label(self.folder_bar, textvariable=self.selection_text, foreground='#555').pack(side='left', padx=8)
        self.tree.bind('<Button-1>', self.batch_click, add='+')
        self.tree.bind('<<TreeviewSelect>>', lambda _event: self.update_selection_status(), add='+')

    def batch_click(self, event):
        if not self.batch_select_mode.get():
            return None
        iid = self.tree.identify_row(event.y)
        if not iid:
            return 'break'
        self.toggle_item_selection(iid)
        self.tree.focus(iid)
        self.update_selection_status()
        return 'break'

    def toggle_item_selection(self, iid):
        if iid in self.tree.selection(): self.tree.selection_remove(iid)
        else: self.tree.selection_add(iid)

    def select_all_visible(self):
        children = self.tree.get_children('')
        if children: self.tree.selection_set(children)
        self.update_selection_status()

    def clear_selection(self):
        selected = self.tree.selection()
        if selected: self.tree.selection_remove(*selected)
        self.update_selection_status()

    def update_selection_status(self):
        mode = ' · 点击即可继续多选' if self.batch_select_mode.get() else ''
        self.selection_text.set(f'已选择 {len(self.tree.selection())} 个{mode}')

    def render(self):
        super().render()
        if hasattr(self, 'selection_text'): self.update_selection_status()


BatchSelectMediaOrganizerApp().mainloop()
