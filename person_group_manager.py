import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk


LABELS_FILE = Path(__file__).resolve().parent / 'test-results' / 'person-labels.json'


def _load_overrides():
    try:
        return json.loads(LABELS_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def apply_saved_person_labels(rows):
    overrides = _load_overrides()
    for row in rows:
        saved = overrides.get(str(row.get('p', '')))
        if saved is not None:
            row['people'] = set(saved)
            row['people_text'] = '、'.join(sorted(row['people'])) or '无人脸'


def save_person_labels(rows, changed_paths):
    overrides = _load_overrides()
    for row in rows:
        key = str(row.get('p', ''))
        if key in changed_paths:
            overrides[key] = sorted(row.get('people', set()))
    LABELS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LABELS_FILE.write_text(json.dumps(overrides, ensure_ascii=False, indent=2), encoding='utf-8')


class PersonGroupManager(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.changed_paths = set()
        self.title('模特分类管理')
        self.geometry('980x650')
        self.minsize(760, 500)
        self.transient(app)
        self.protocol('WM_DELETE_WINDOW', self.close)

        self.summary = tk.StringVar()
        ttk.Label(self, textvariable=self.summary, font=('Segoe UI', 12, 'bold'), padding=(12, 12, 12, 6)).pack(fill='x')
        ttk.Label(self, text='左侧选择模特分类，右侧查看所属素材；所有人工调整都会保存。', foreground='#666', padding=(12, 0, 12, 10)).pack(fill='x')

        body = ttk.Panedwindow(self, orient='horizontal')
        body.pack(fill='both', expand=True, padx=12)
        left = ttk.Frame(body, padding=6)
        right = ttk.Frame(body, padding=6)
        body.add(left, weight=1)
        body.add(right, weight=3)

        ttk.Label(left, text='模特分类（可多选后合并）').pack(anchor='w', pady=(0, 5))
        self.groups = tk.Listbox(left, selectmode='extended', exportselection=False)
        self.groups.pack(fill='both', expand=True)
        self.groups.bind('<<ListboxSelect>>', lambda _event: self.refresh_files())

        group_actions = ttk.Frame(left)
        group_actions.pack(fill='x', pady=6)
        ttk.Button(group_actions, text='重命名', command=self.rename_group).pack(side='left')
        ttk.Button(group_actions, text='合并所选组', command=self.merge_groups).pack(side='left', padx=5)

        ttk.Label(right, text='当前分类中的素材').pack(anchor='w', pady=(0, 5))
        self.files = ttk.Treeview(right, columns=('file', 'kind'), show='headings', selectmode='extended')
        self.files.heading('file', text='文件')
        self.files.heading('kind', text='类型')
        self.files.column('file', width=520, anchor='w')
        self.files.column('kind', width=70, anchor='center')
        self.files.pack(fill='both', expand=True)
        self.files.bind('<Double-1>', lambda _event: self.locate_in_main_table())

        material_actions = ttk.Frame(right)
        material_actions.pack(fill='x', pady=6)
        ttk.Button(material_actions, text='在主表定位', command=self.locate_in_main_table).pack(side='left')
        ttk.Button(material_actions, text='将主表选中素材加入此组', command=self.add_main_selection).pack(side='left', padx=5)
        ttk.Button(material_actions, text='从此组移除右侧所选素材', command=self.remove_files).pack(side='left')
        ttk.Button(material_actions, text='用主表选中素材新建模特组', command=self.create_group).pack(side='right')

        footer = ttk.Frame(self, padding=12)
        footer.pack(fill='x')
        ttk.Button(footer, text='完成', command=self.close).pack(side='right')
        self.refresh()

    def group_names(self):
        return sorted({name for row in self.app.rows for name in row.get('people', set())})

    def selected_groups(self):
        return [self.groups.get(index).rsplit('  (', 1)[0] for index in self.groups.curselection()]

    def selected_main_rows(self):
        rows = []
        for iid in self.app.tree.selection():
            try:
                rows.append(self.app.rows[int(iid)])
            except (ValueError, IndexError):
                pass
        return rows

    def refresh(self, select_name=None):
        names = self.group_names()
        faces = sum(len(row.get('faces', [])) for row in self.app.rows)
        grouped_files = sum(bool(row.get('people')) for row in self.app.rows)
        self.summary.set(f'识别到 {faces} 张人脸 · {len(names)} 个模特分类 · {grouped_files} 个含人物素材')
        self.groups.delete(0, 'end')
        target = None
        for index, name in enumerate(names):
            count = sum(name in row.get('people', set()) for row in self.app.rows)
            self.groups.insert('end', f'{name}  ({count} 个素材)')
            if name == select_name:
                target = index
        if target is not None:
            self.groups.selection_set(target)
            self.groups.see(target)
        elif names:
            self.groups.selection_set(0)
        self.refresh_files()

    def refresh_files(self):
        self.files.delete(*self.files.get_children())
        names = self.selected_groups()
        if not names:
            return
        for index, row in enumerate(self.app.rows):
            if any(name in row.get('people', set()) for name in names):
                self.files.insert('', 'end', iid=str(index), values=(row['p'].name, row.get('kind', '')))

    def require_one_group(self):
        names = self.selected_groups()
        if len(names) != 1:
            messagebox.showinfo('请选择一个分类', '请先在左侧选择一个模特分类。', parent=self)
            return None
        return names[0]

    def rename_group(self):
        old = self.require_one_group()
        if not old:
            return
        new = simpledialog.askstring('模特命名', f'将“{old}”重命名为：', initialvalue=old, parent=self)
        if not new or new.strip() == old:
            return
        new = new.strip()
        for row in self.app.rows:
            people = row.get('people', set())
            if old in people:
                people.discard(old); people.add(new); self.mark(row)
        self.finish_change(new)

    def merge_groups(self):
        names = self.selected_groups()
        if len(names) < 2:
            messagebox.showinfo('请选择多个分类', '按住 Ctrl 选择两个或更多模特分类后再合并。', parent=self)
            return
        target = simpledialog.askstring('合并模特分类', '合并后的模特名称：', initialvalue=names[0], parent=self)
        if not target:
            return
        target = target.strip()
        for row in self.app.rows:
            people = row.get('people', set())
            if any(name in people for name in names):
                people.difference_update(names); people.add(target); self.mark(row)
        self.finish_change(target)

    def add_main_selection(self):
        name = self.require_one_group()
        if not name:
            return
        rows = self.selected_main_rows()
        if not rows:
            messagebox.showinfo('主表未选择素材', '请先在主界面的表格中选择要加入该模特分类的素材。', parent=self)
            return
        for row in rows:
            row.setdefault('people', set()).add(name); self.mark(row)
        self.finish_change(name)

    def create_group(self):
        rows = self.selected_main_rows()
        if not rows:
            messagebox.showinfo('主表未选择素材', '请先在主界面的表格中选择素材，再新建模特分类。', parent=self)
            return
        name = simpledialog.askstring('新建模特分类', '模特名称：', parent=self)
        if not name:
            return
        name = name.strip()
        for row in rows:
            row.setdefault('people', set()).add(name); self.mark(row)
        self.finish_change(name)

    def remove_files(self):
        name = self.require_one_group()
        if not name:
            return
        selected = self.files.selection()
        if not selected:
            messagebox.showinfo('未选择素材', '请在右侧选择要从此分类移除的素材。', parent=self)
            return
        for iid in selected:
            row = self.app.rows[int(iid)]
            row.get('people', set()).discard(name); self.mark(row)
        self.finish_change(name)

    def locate_in_main_table(self):
        selected = self.files.selection()
        if not selected:
            messagebox.showinfo('未选择素材', '请先在右侧选择素材。', parent=self)
            return
        visible = set(self.app.tree.get_children(''))
        self.app.tree.selection_remove(*self.app.tree.selection())
        found = [iid for iid in selected if iid in visible]
        if not found:
            messagebox.showinfo('当前筛选中不可见', '该素材不在主表当前筛选结果中，请把主表筛选改为“全部”。', parent=self)
            return
        self.app.tree.selection_set(found)
        self.app.tree.focus(found[0]); self.app.tree.see(found[0])
        self.app.lift()

    def mark(self, row):
        row['people_text'] = '、'.join(sorted(row.get('people', set()))) or '无人脸'
        self.changed_paths.add(str(row['p']))

    def finish_change(self, selected_name=None):
        save_person_labels(self.app.rows, self.changed_paths)
        self.app.render()
        self.refresh(selected_name)

    def close(self):
        save_person_labels(self.app.rows, self.changed_paths)
        self.destroy()
