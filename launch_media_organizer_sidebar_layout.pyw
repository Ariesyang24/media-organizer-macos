import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_natural_drop.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('NaturalDropMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
NaturalDropMediaOrganizerApp = scope['NaturalDropMediaOrganizerApp']


class SidebarLayoutMediaOrganizerApp(NaturalDropMediaOrganizerApp):
    MIN_SIDEBAR_WIDTH = 170
    MAX_SIDEBAR_WIDTH = 520

    def __init__(self):
        super().__init__()
        self.sidebar_targets = []
        self.sidebar_start_x = 0
        self.sidebar_start_width = 230
        self.sidebar = ttk.Frame(self.preview, width=230, relief='groove', padding=(6, 6))
        self.sidebar.pack(side='left', fill='y', padx=(8, 3), pady=(0, 4), before=self.folder_area)
        self.sidebar.pack_propagate(False)
        top = ttk.Frame(self.sidebar); top.pack(fill='x')
        ttk.Label(top, text='文件夹列表', font=('Segoe UI', 10, 'bold')).pack(side='left')
        self.sidebar_count = tk.StringVar(); ttk.Label(top, textvariable=self.sidebar_count, foreground='#666').pack(side='right')
        list_area = ttk.Frame(self.sidebar); list_area.pack(fill='both', expand=True, pady=(6, 0))
        self.sidebar_list = tk.Listbox(list_area, exportselection=False, activestyle='dotbox')
        self.sidebar_list.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(list_area, orient='vertical', command=self.sidebar_list.yview)
        scroll.pack(side='right', fill='y'); self.sidebar_list.configure(yscrollcommand=scroll.set)
        self.sidebar_list.bind('<<ListboxSelect>>', self.sidebar_select)
        self.sidebar_list.bind('<Double-1>', self.sidebar_select)
        self.sidebar_list.bind('<Button-3>', self.sidebar_context_menu)
        self.sidebar_list.bind('<MouseWheel>', self.sidebar_mousewheel)
        self.sidebar_grip = ttk.Frame(self.preview, width=9, cursor='sb_h_double_arrow')
        self.sidebar_grip.pack(side='left', fill='y', before=self.folder_area)
        self.sidebar_grip.pack_propagate(False)
        ttk.Separator(self.sidebar_grip, orient='vertical').pack(fill='y', expand=True, padx=3)
        self.sidebar_grip.bind('<ButtonPress-1>', self.start_sidebar_resize)
        self.sidebar_grip.bind('<B1-Motion>', self.resize_sidebar)
        for child in self.sidebar_grip.winfo_children():
            child.bind('<ButtonPress-1>', self.start_sidebar_resize)
            child.bind('<B1-Motion>', self.resize_sidebar)
        self.refresh_sidebar()

    def refresh_sidebar(self):
        if not hasattr(self, 'sidebar_list'): return
        selected_target = None
        current = self.sidebar_list.curselection()
        if current and current[0] < len(self.sidebar_targets): selected_target = self.sidebar_targets[current[0]][1]
        self.sidebar_list.delete(0, 'end'); self.sidebar_targets = []
        groups = self.output_directories()
        for target, rows in sorted(groups.items()):
            custom = '自定义分类' in Path(target).parts
            prefix = '★' if custom else '📁'
            self.sidebar_targets.append(('target', target))
            self.sidebar_list.insert('end', f'{prefix} {Path(target).name}  ({len(rows)})\n   {target}')
        represented = {Path(target).parts[-1] for target in groups if '自定义分类' in Path(target).parts}
        for name in self.folder_names():
            if name not in represented:
                self.sidebar_targets.append(('empty', name))
                self.sidebar_list.insert('end', f'☆ {name}  (空文件夹)')
        self.sidebar_count.set(str(len(self.sidebar_targets)))
        if selected_target is not None:
            for index, (_, value) in enumerate(self.sidebar_targets):
                if value == selected_target: self.sidebar_list.selection_set(index); self.sidebar_list.see(index); break

    def sidebar_select(self, _event=None):
        selected = self.sidebar_list.curselection()
        if not selected: return
        kind, value = self.sidebar_targets[selected[0]]
        if kind == 'target': self.select_directory_rows(value)
        else: self.select_custom_folder_rows(value)

    def sidebar_context_menu(self, event):
        index = self.sidebar_list.nearest(event.y)
        if index < 0 or index >= len(self.sidebar_targets): return
        self.sidebar_list.selection_clear(0, 'end'); self.sidebar_list.selection_set(index)
        kind, value = self.sidebar_targets[index]
        if kind == 'target': self.show_any_folder_menu(event, value)
        else: self.show_folder_card_menu(event, value)

    def sidebar_mousewheel(self, event):
        self.sidebar_list.yview_scroll((-1 if event.delta > 0 else 1) * 3, 'units')
        return 'break'

    def start_sidebar_resize(self, event):
        self.sidebar_start_x = event.x_root
        self.sidebar_start_width = self.sidebar.winfo_width()

    def resize_sidebar(self, event):
        width = self.sidebar_start_width + event.x_root - self.sidebar_start_x
        width = max(self.MIN_SIDEBAR_WIDTH, min(self.MAX_SIDEBAR_WIDTH, width))
        self.sidebar.configure(width=width)

    def finish_row_drag(self, event):
        if not self.drag_active: return
        widget = self.winfo_containing(event.x_root, event.y_root)
        if widget == getattr(self, 'sidebar_list', None):
            self.drag_active = False; self.tree.configure(cursor='')
            index = self.sidebar_list.nearest(event.y_root - self.sidebar_list.winfo_rooty())
            rows = self.selected_rows()
            if rows and 0 <= index < len(self.sidebar_targets):
                kind, value = self.sidebar_targets[index]
                if kind == 'empty': self.drop_rows(rows, value)
                elif '自定义分类' in Path(value).parts: self.drop_rows(rows, Path(value).parts[-1])
                else: self.drop_rows(rows, '__AUTO__')
            return
        super().finish_row_drag(event)

    def rebuild_folder_cards(self):
        super().rebuild_folder_cards()
        self.refresh_sidebar()

    def render(self):
        super().render()
        self.refresh_sidebar()


SidebarLayoutMediaOrganizerApp().mainloop()
