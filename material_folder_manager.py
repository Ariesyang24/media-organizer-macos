import json
import re
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk


FOLDERS_FILE = Path(__file__).resolve().parent / 'test-results' / 'material-folders.json'


def _load():
    try:
        return json.loads(FOLDERS_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def apply_saved_material_folders(rows):
    saved = _load()
    for row in rows:
        row['custom_folder'] = saved.get(str(row.get('p', '')), '')


def apply_custom_targets(rows):
    for row in rows:
        folder = row.get('custom_folder', '').strip()
        if folder:
            row['target'] = str(Path('自定义分类') / folder)


def save_material_folders(rows, changed_paths):
    saved = _load()
    for row in rows:
        key = str(row.get('p', ''))
        if key not in changed_paths:
            continue
        folder = row.get('custom_folder', '').strip()
        if folder:
            saved[key] = folder
        else:
            saved.pop(key, None)
    FOLDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    FOLDERS_FILE.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding='utf-8')


def valid_folder_name(value):
    value = (value or '').strip()
    if not value or value in {'.', '..'} or re.search(r'[\\/:*?"<>|]', value):
        return None
    return value


class MaterialFolderManager(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.changed_paths = set()
        self.title('素材文件夹管理')
        self.geometry('980x650')
        self.minsize(760, 500)
        self.transient(app)
        self.protocol('WM_DELETE_WINDOW', self.close)

        self.summary = tk.StringVar()
        ttk.Label(self, textvariable=self.summary, font=('Segoe UI', 12, 'bold'), padding=(12, 12, 12, 6)).pack(fill='x')
        ttk.Label(self, text='先在主表多选素材，再新建文件夹或移动到已有文件夹；执行整理后会放入“自定义分类”目录。', foreground='#666', padding=(12, 0, 12, 10)).pack(fill='x')
        body = ttk.Panedwindow(self, orient='horizontal'); body.pack(fill='both', expand=True, padx=12)
        left = ttk.Frame(body, padding=6); right = ttk.Frame(body, padding=6)
        body.add(left, weight=1); body.add(right, weight=3)

        ttk.Label(left, text='自建素材文件夹').pack(anchor='w', pady=(0, 5))
        self.folders = tk.Listbox(left, exportselection=False)
        self.folders.pack(fill='both', expand=True)
        self.folders.bind('<<ListboxSelect>>', lambda _event: self.refresh_files())
        actions = ttk.Frame(left); actions.pack(fill='x', pady=6)
        ttk.Button(actions, text='新建文件夹', command=self.create_folder).pack(side='left')
        ttk.Button(actions, text='重命名', command=self.rename_folder).pack(side='left', padx=5)
        ttk.Button(actions, text='删除分类', command=self.delete_folder).pack(side='left')

        ttk.Label(right, text='当前文件夹中的素材').pack(anchor='w', pady=(0, 5))
        self.files = ttk.Treeview(right, columns=('file', 'kind'), show='headings', selectmode='extended')
        self.files.heading('file', text='文件'); self.files.heading('kind', text='类型')
        self.files.column('file', width=520, anchor='w'); self.files.column('kind', width=70, anchor='center')
        self.files.pack(fill='both', expand=True)
        bar = ttk.Frame(right); bar.pack(fill='x', pady=6)
        ttk.Button(bar, text='将主表选中素材移入此文件夹', command=self.assign_selection).pack(side='left')
        ttk.Button(bar, text='移出右侧所选素材', command=self.remove_selected).pack(side='left', padx=5)
        ttk.Button(bar, text='在主表定位', command=self.locate).pack(side='left')
        footer = ttk.Frame(self, padding=12); footer.pack(fill='x')
        ttk.Button(footer, text='完成', command=self.close).pack(side='right')
        self.refresh()

    def folder_names(self):
        return sorted({row.get('custom_folder', '') for row in self.app.rows if row.get('custom_folder')})

    def current_folder(self):
        selected = self.folders.curselection()
        if not selected:
            messagebox.showinfo('请选择文件夹', '请先在左侧选择一个素材文件夹。', parent=self); return None
        return self.folders.get(selected[0]).rsplit('  (', 1)[0]

    def main_rows(self):
        result = []
        for iid in self.app.tree.selection():
            try: result.append(self.app.rows[int(iid)])
            except (ValueError, IndexError): pass
        return result

    def ask_name(self, title, initial=''):
        name = valid_folder_name(simpledialog.askstring(title, '文件夹名称：', initialvalue=initial, parent=self))
        if not name:
            messagebox.showinfo('名称不可用', '请输入有效名称，且不要包含 \\ / : * ? " < > |。', parent=self)
        return name

    def refresh(self, select_name=None):
        names = self.folder_names(); assigned = sum(bool(r.get('custom_folder')) for r in self.app.rows)
        self.summary.set(f'{len(names)} 个自建文件夹 · {assigned} 个已分类素材 · {len(self.app.rows)-assigned} 个按自动规则整理')
        self.folders.delete(0, 'end'); target = None
        for index, name in enumerate(names):
            count = sum(r.get('custom_folder') == name for r in self.app.rows)
            self.folders.insert('end', f'{name}  ({count} 个素材)')
            if name == select_name: target = index
        if target is not None: self.folders.selection_set(target); self.folders.see(target)
        elif names: self.folders.selection_set(0)
        self.refresh_files()

    def refresh_files(self):
        self.files.delete(*self.files.get_children())
        selected = self.folders.curselection()
        if not selected: return
        name = self.folders.get(selected[0]).rsplit('  (', 1)[0]
        for index, row in enumerate(self.app.rows):
            if row.get('custom_folder') == name:
                self.files.insert('', 'end', iid=str(index), values=(row['p'].name, row.get('kind', '')))

    def create_folder(self):
        name = self.ask_name('新建素材文件夹')
        if not name: return
        rows = self.main_rows()
        if not rows:
            messagebox.showinfo('文件夹已创建', '文件夹已创建。请回到主表选择素材，再点“移入此文件夹”。', parent=self)
        for row in rows: self.assign(row, name)
        if not rows:
            # Keep an empty folder visible for this session by using a marker only in the manager.
            messagebox.showinfo('提示', '空文件夹会在放入第一份素材后保存。', parent=self)
        self.finish(name)

    def assign_selection(self):
        name = self.current_folder()
        if not name: return
        rows = self.main_rows()
        if not rows:
            messagebox.showinfo('主表未选择素材', '请先在主界面的表格中选择要分类的素材。', parent=self); return
        for row in rows: self.assign(row, name)
        self.finish(name)

    def remove_selected(self):
        selected = self.files.selection()
        if not selected:
            messagebox.showinfo('未选择素材', '请在右侧选择要移出自建文件夹的素材。', parent=self); return
        current = self.current_folder()
        for iid in selected:
            row = self.app.rows[int(iid)]
            if row.get('custom_folder') == current: self.assign(row, '')
        self.finish(current)

    def rename_folder(self):
        old = self.current_folder()
        if not old: return
        new = self.ask_name('重命名素材文件夹', old)
        if not new or new == old: return
        for row in self.app.rows:
            if row.get('custom_folder') == old: self.assign(row, new)
        self.finish(new)

    def delete_folder(self):
        name = self.current_folder()
        if not name: return
        if not messagebox.askyesno('删除分类', f'删除“{name}”分类？\n素材不会被删除，将恢复自动整理规则。', parent=self): return
        for row in self.app.rows:
            if row.get('custom_folder') == name: self.assign(row, '')
        self.finish()

    def locate(self):
        selected = self.files.selection()
        if not selected:
            messagebox.showinfo('未选择素材', '请先在右侧选择素材。', parent=self); return
        visible = set(self.app.tree.get_children('')); found = [iid for iid in selected if iid in visible]
        if not found:
            messagebox.showinfo('当前筛选中不可见', '请把主表筛选改为“全部”后再定位。', parent=self); return
        self.app.tree.selection_remove(*self.app.tree.selection()); self.app.tree.selection_set(found)
        self.app.tree.focus(found[0]); self.app.tree.see(found[0]); self.app.lift()

    def assign(self, row, folder):
        row['custom_folder'] = folder; self.changed_paths.add(str(row['p']))

    def finish(self, name=None):
        save_material_folders(self.app.rows, self.changed_paths)
        self.app.render(); self.refresh(name)

    def close(self):
        save_material_folders(self.app.rows, self.changed_paths); self.destroy()
