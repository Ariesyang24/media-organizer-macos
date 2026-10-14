import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

from material_folder_manager import save_material_folders, valid_folder_name

launcher = root / 'launch_media_organizer_manager_v3.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('ManagerV3MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
ManagerV3MediaOrganizerApp = scope['ManagerV3MediaOrganizerApp']


class InlineFolderMediaOrganizerApp(ManagerV3MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self._hide_material_manager_button(self)
        self.folder_choice = tk.StringVar()
        self.folder_summary = tk.StringVar(value='自定义文件夹：0 个')
        self.folder_bar = ttk.Frame(self.preview, padding=(8, 5))
        self.folder_bar.pack(fill='x', before=self.tree)
        ttk.Label(self.folder_bar, textvariable=self.folder_summary, font=('Segoe UI', 10, 'bold')).pack(side='left')
        ttk.Button(self.folder_bar, text='+ 新建文件夹并放入选中素材', command=self.new_folder_for_selection).pack(side='left', padx=(12, 6))
        ttk.Label(self.folder_bar, text='移入：').pack(side='left')
        self.folder_box = ttk.Combobox(self.folder_bar, textvariable=self.folder_choice, state='readonly', width=20)
        self.folder_box.pack(side='left', padx=4)
        ttk.Button(self.folder_bar, text='移入所选文件夹', command=self.move_selection_to_choice).pack(side='left')
        ttk.Button(self.folder_bar, text='移出自定义文件夹', command=self.remove_selection_from_folder).pack(side='left', padx=6)
        ttk.Label(self.folder_bar, text='也可以多选素材后点击鼠标右键', foreground='#666').pack(side='right')
        self.folder_menu = tk.Menu(self, tearoff=False)
        self.tree.bind('<Button-3>', self.show_folder_menu, add='+')
        self.refresh_folder_controls()

    def _hide_material_manager_button(self, widget):
        for child in widget.winfo_children():
            try:
                if child.winfo_class() == 'TButton' and str(child.cget('text')) == '素材文件夹管理':
                    child.pack_forget()
            except Exception:
                pass
            self._hide_material_manager_button(child)

    def selected_rows(self):
        rows = []
        for iid in self.tree.selection():
            try: rows.append(self.rows[int(iid)])
            except (ValueError, IndexError): pass
        return rows

    def folder_names(self):
        return sorted({row.get('custom_folder', '') for row in self.rows if row.get('custom_folder')})

    def refresh_folder_controls(self):
        names = self.folder_names()
        self.folder_box.configure(values=names)
        if names and self.folder_choice.get() not in names: self.folder_choice.set(names[0])
        if not names: self.folder_choice.set('')
        assigned = sum(bool(row.get('custom_folder')) for row in self.rows)
        self.folder_summary.set(f'自定义文件夹：{len(names)} 个 · 已分类 {assigned} 个素材')

    def require_selection(self):
        rows = self.selected_rows()
        if not rows:
            messagebox.showinfo('请先选择素材', '请在下方表格中选择一个或多个素材。\n可按住 Ctrl 或 Shift 多选。', parent=self)
        return rows

    def new_folder_for_selection(self):
        rows = self.require_selection()
        if not rows: return
        name = valid_folder_name(simpledialog.askstring('新建素材文件夹', '文件夹名称：', parent=self))
        if not name:
            messagebox.showinfo('名称不可用', '请输入有效名称，且不要包含 \\ / : * ? " < > |。', parent=self); return
        self.assign_rows(rows, name)

    def move_selection_to_choice(self):
        rows = self.require_selection(); name = self.folder_choice.get().strip()
        if not rows: return
        if not name:
            messagebox.showinfo('没有可选文件夹', '请先新建一个自定义文件夹。', parent=self); return
        self.assign_rows(rows, name)

    def remove_selection_from_folder(self):
        rows = self.require_selection()
        if rows: self.assign_rows(rows, '')

    def assign_rows(self, rows, folder):
        changed = set()
        for row in rows:
            row['custom_folder'] = folder
            changed.add(str(row['p']))
        save_material_folders(self.rows, changed)
        self.render()
        if folder: self.folder_choice.set(folder)
        self.refresh_folder_controls()
        self.status.set(f'已将 {len(rows)} 个素材放入“{folder}”' if folder else f'已将 {len(rows)} 个素材恢复为自动分类')

    def show_folder_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid and iid not in self.tree.selection():
            self.tree.selection_set(iid); self.tree.focus(iid)
        self.folder_menu.delete(0, 'end')
        self.folder_menu.add_command(label='新建文件夹并放入选中素材…', command=self.new_folder_for_selection)
        move = tk.Menu(self.folder_menu, tearoff=False)
        names = self.folder_names()
        if names:
            for name in names: move.add_command(label=name, command=lambda value=name: self.assign_rows(self.require_selection(), value) if self.selected_rows() else None)
        else:
            move.add_command(label='暂无自定义文件夹', state='disabled')
        self.folder_menu.add_cascade(label='移入已有文件夹', menu=move)
        self.folder_menu.add_separator()
        self.folder_menu.add_command(label='移出自定义文件夹（恢复自动分类）', command=self.remove_selection_from_folder)
        if hasattr(self, 'remove_selected_from_plan'):
            count = len(self.tree.selection())
            self.folder_menu.add_separator()
            self.folder_menu.add_command(label=f'从本次整理中删除（{count} 个）', command=self.remove_selected_from_plan)
        if iid: self.folder_menu.tk_popup(event.x_root, event.y_root)

    def render(self):
        super().render()
        if hasattr(self, 'folder_box'): self.refresh_folder_controls()


InlineFolderMediaOrganizerApp().mainloop()
