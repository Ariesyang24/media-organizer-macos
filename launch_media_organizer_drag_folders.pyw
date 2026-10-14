import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

from material_folder_manager import save_material_folders

launcher = root / 'launch_media_organizer_batch_select.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('BatchSelectMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
BatchSelectMediaOrganizerApp = scope['BatchSelectMediaOrganizerApp']


class DragFolderMediaOrganizerApp(BatchSelectMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.drag_active = False
        self.drag_hint = tk.StringVar(value='拖动下方选中素材到文件夹卡片；拖到“自动分类”或空白处可移出自定义文件夹')
        self.folder_area = ttk.LabelFrame(self.preview, text='识别后的素材文件夹（可拖动调整）', padding=6)
        self.folder_area.pack(fill='x', padx=8, pady=(4, 2), before=self.folder_bar)
        header = ttk.Frame(self.folder_area); header.pack(fill='x')
        ttk.Label(header, textvariable=self.drag_hint, foreground='#555').pack(side='left')
        self.directory_count = tk.StringVar()
        ttk.Label(header, textvariable=self.directory_count, font=('Segoe UI', 9, 'bold')).pack(side='right')
        body = ttk.Frame(self.folder_area); body.pack(fill='x', pady=(5, 0))
        body._drop_folder = '__AUTO__'
        self.folder_canvas = tk.Canvas(body, height=132, highlightthickness=0)
        self.folder_canvas.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(body, orient='vertical', command=self.folder_canvas.yview)
        scrollbar.pack(side='right', fill='y')
        self.folder_canvas.configure(yscrollcommand=scrollbar.set)
        self.folder_cards = ttk.Frame(self.folder_canvas)
        self.folder_cards._drop_folder = '__AUTO__'
        self.folder_window = self.folder_canvas.create_window((0, 0), window=self.folder_cards, anchor='nw')
        self.folder_cards.bind('<Configure>', lambda _event: self.folder_canvas.configure(scrollregion=self.folder_canvas.bbox('all')))
        self.folder_canvas.bind('<Configure>', lambda event: self.folder_canvas.itemconfigure(self.folder_window, width=event.width))
        self.tree.bind('<B1-Motion>', self.start_row_drag, add='+')
        self.tree.bind('<ButtonRelease-1>', self.finish_row_drag, add='+')
        self.rebuild_folder_cards()

    def output_directories(self):
        groups = {}
        for row in self.rows:
            target = row.get('target', '')
            if target: groups.setdefault(target, []).append(row)
        return groups

    def rebuild_folder_cards(self):
        for child in self.folder_cards.winfo_children(): child.destroy()
        groups = self.output_directories()
        auto_count = sum('自定义分类' not in Path(target).parts for target in groups)
        custom_count = len(groups) - auto_count
        self.directory_count.set(f'{len(groups)} 个目录 · 自动 {auto_count} · 自建 {custom_count}')
        auto = ttk.Button(self.folder_cards, text='↩ 自动分类\n拖到这里移出自定义文件夹', command=lambda: None)
        auto._drop_folder = '__AUTO__'; auto.grid(row=0, column=0, sticky='nsew', padx=3, pady=3, ipadx=5, ipady=7)
        for position, (target, rows) in enumerate(sorted(groups.items()), 1):
            parts = Path(target).parts
            custom = '自定义分类' in parts
            folder = parts[-1] if custom else '__AUTO__'
            prefix = '★ 自定义' if custom else '📁 自动'
            text = f'{prefix} · {len(rows)} 个素材\n{target}'
            card = ttk.Button(self.folder_cards, text=text, command=lambda value=target: self.select_directory_rows(value))
            card._drop_folder = folder
            row_index, column = divmod(position, 3)
            card.grid(row=row_index, column=column, sticky='nsew', padx=3, pady=3, ipadx=5, ipady=5)
        for column in range(3): self.folder_cards.columnconfigure(column, weight=1, uniform='folder')

    def select_directory_rows(self, target):
        matching = []
        visible = set(self.tree.get_children(''))
        for index, row in enumerate(self.rows):
            iid = str(index)
            if iid in visible and row.get('target') == target: matching.append(iid)
        self.tree.selection_remove(*self.tree.selection())
        if matching:
            self.tree.selection_set(matching); self.tree.focus(matching[0]); self.tree.see(matching[0])
        self.update_selection_status()
        self.status.set(f'已选择目录中的 {len(matching)} 个可见素材：{target}')

    def start_row_drag(self, _event):
        if self.tree.selection():
            self.drag_active = True
            self.tree.configure(cursor='fleur')
            self.drag_hint.set(f'正在拖动 {len(self.tree.selection())} 个素材，请放到上方文件夹卡片')

    def finish_row_drag(self, event):
        if not self.drag_active: return
        self.drag_active = False; self.tree.configure(cursor='')
        widget = self.winfo_containing(event.x_root, event.y_root)
        folder = self.folder_drop_value(widget)
        if folder is not None:
            rows = self.selected_rows()
            if rows: self.drop_rows(rows, folder)
        else:
            self.drag_hint.set('未放入文件夹；素材分类保持不变')

    def folder_drop_value(self, widget):
        current = widget
        while current is not None:
            if hasattr(current, '_drop_folder'): return current._drop_folder
            if current == self: break
            current = getattr(current, 'master', None)
        return None

    def drop_rows(self, rows, folder):
        target_folder = '' if folder == '__AUTO__' else folder
        changed = set()
        for row in rows:
            row['custom_folder'] = target_folder; changed.add(str(row['p']))
        save_material_folders(self.rows, changed)
        self.render()
        if target_folder:
            self.folder_choice.set(target_folder)
            self.status.set(f'已拖动 {len(rows)} 个素材到“{target_folder}”')
            self.drag_hint.set(f'已保存：{len(rows)} 个素材 → {target_folder}')
        else:
            self.status.set(f'已将 {len(rows)} 个素材移出自定义文件夹，恢复自动分类')
            self.drag_hint.set(f'已移出：{len(rows)} 个素材恢复自动分类')

    def render(self):
        super().render()
        if hasattr(self, 'folder_cards'): self.rebuild_folder_cards()


DragFolderMediaOrganizerApp().mainloop()
