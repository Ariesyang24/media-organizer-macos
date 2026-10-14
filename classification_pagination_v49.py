import json
import math
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog

from material_folder_manager import save_material_folders, valid_folder_name
from project_folder_catalog import add_project_folder, load_project_folders, save_project_folders, rename_project_folder
from v3_ui_components import COLORS, CanvasButton


class ClassificationPaginationV49:
    SETTINGS = Path(__file__).resolve().parent / 'media_organizer_v3_ui.json'

    def __init__(self, app):
        self.app = app
        self.ws = app.unified_workspace
        self.page = 0
        self.page_size = 20
        self.filtered_ids = []
        self.drag_start = None
        self.dragging = False
        self.drag_target = None
        self.favorite_names = set()
        self._load_favorites()
        self._wrap_refresh()
        self._wrap_undo()
        self._install_pager()
        self._install_category_actions()
        self._install_category_creator()
        self._install_drag()
        self.refresh_categories()
        self.apply_page(reset=True)

    def _load_favorites(self):
        try:
            data = json.loads(self.SETTINGS.read_text(encoding='utf-8'))
            self.favorite_names = set(data.get('favorite_categories', []))
        except Exception:
            self.favorite_names = set()

    def _save_favorites(self):
        try:
            data = json.loads(self.SETTINGS.read_text(encoding='utf-8')) if self.SETTINGS.exists() else {}
        except Exception:
            data = {}
        data['favorite_categories'] = sorted(self.favorite_names)
        self.SETTINGS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def _wrap_refresh(self):
        self.original_apply_filter = self.app.apply_filter
        self.original_render = self.app.render
        self.original_refresh_sidebar = self.app.refresh_sidebar

        def apply_filter():
            self.original_apply_filter()
            self.apply_page(reset=True, already_filtered=True)

        def render():
            self.original_render()
            self.original_apply_filter()
            self.apply_page(reset=False, already_filtered=True)

        def refresh_sidebar():
            self.original_refresh_sidebar()
            self.refresh_categories()

        self.app.apply_filter = apply_filter
        self.app.render = render
        self.app.refresh_sidebar = refresh_sidebar

        self.original_select_filtered = self.ws.select_filtered
        self.ws.select_filtered = self.select_all_filtered

    def _wrap_undo(self):
        self.original_undo = self.ws.undo

        def undo():
            action = self.ws.undo_stack[-1] if self.ws.undo_stack else None
            if isinstance(action, dict) and 'catalog_before' in action:
                save_project_folders(self.app.sources, action['catalog_before'])
            if isinstance(action, dict) and 'favorite_before' in action:
                self.favorite_names = set(action['favorite_before']); self._save_favorites()
            self.original_undo()
            if isinstance(action, dict) and 'rows' in action:
                changed = {str(self.app.rows[index]['p']) for index in action['rows'] if index < len(self.app.rows)}
                if changed:
                    save_material_folders(self.app.rows, changed)
            self.refresh_categories()

        self.ws.undo = undo
    def _find_footer(self):
        variable = str(self.app.v3_selection_text)
        for widget in self.app._descendants(self.app.v3_recognition_root):
            try:
                if widget.winfo_class() == 'Label' and str(widget.cget('textvariable')) == variable:
                    return widget.master
            except tk.TclError:
                pass
        return None

    def _install_pager(self):
        foot = self._find_footer()
        if foot is None:
            return
        self.pager = tk.Frame(foot, bg='white')
        self.pager.pack(side='right', padx=(8, 70))
        self.page_text = tk.StringVar(value='第 1 / 1 页')
        self.page_size_btn = CanvasButton(self.pager, '20 条/页', width=86, height=30,
                                          command=self.show_page_size)
        self.page_size_btn.pack(side='left', padx=3)
        self.prev_btn = CanvasButton(self.pager, '', icon='chevron-left', width=32, height=30,
                                     command=lambda: self.change_page(-1))
        self.prev_btn.pack(side='left', padx=2)
        tk.Label(self.pager, textvariable=self.page_text, bg='white', fg=COLORS['muted'],
                 font=('Segoe UI', 8)).pack(side='left', padx=5)
        self.next_btn = CanvasButton(self.pager, '', icon='chevron-right', width=32, height=30,
                                     command=lambda: self.change_page(1))
        self.next_btn.pack(side='left', padx=2)
        CanvasButton(self.pager, '选择当前页', width=96, height=30,
                     command=self.select_current_page).pack(side='left', padx=3)

    def show_page_size(self):
        self.app._popup_actions([
            (f'{size} 条/页', lambda value=size: self.set_page_size(value), True)
            for size in (20, 50, 100)
        ], self.page_size_btn)

    def set_page_size(self, value):
        self.page_size = value
        self.page_size_btn.configure(text=f'{value} 条/页')
        self.apply_page(reset=True)

    def apply_page(self, reset=False, already_filtered=False):
        if not already_filtered:
            self.original_apply_filter()
        ids = list(self.app.tree.get_children())
        self.filtered_ids = ids
        if reset:
            self.page = 0
        pages = max(1, math.ceil(len(ids) / self.page_size))
        self.page = min(max(0, self.page), pages - 1)
        start = self.page * self.page_size
        visible = set(ids[start:start + self.page_size])
        for iid in ids:
            if iid not in visible:
                self.app.tree.detach(iid)
        if hasattr(self, 'page_text'):
            self.page_text.set(f'第 {self.page + 1} / {pages} 页')
            self.prev_btn.configure(state='normal' if self.page > 0 else 'disabled')
            self.next_btn.configure(state='normal' if self.page + 1 < pages else 'disabled')
        if hasattr(self.app, 'v3_total_text'):
            self.app.v3_total_text.set(f'共 {len(ids)} 条')
        if hasattr(self.ws, 'filtered_text'):
            self.ws.filtered_text.set(f'当前筛选 {len(ids)} 项')

    def change_page(self, delta):
        target = self.page + delta
        pages = max(1, math.ceil(len(self.filtered_ids) / self.page_size))
        if not 0 <= target < pages:
            return
        self.page = target
        self.original_apply_filter()
        self.apply_page(reset=False, already_filtered=True)

    def select_current_page(self):
        ids = self.app.tree.get_children()
        self.app.tree.selection_set(ids)
        self.app._v3_selection_changed()
        self.app.status.set(f'已选择当前页 {len(ids)} 项素材')

    def select_all_filtered(self):
        # Preserve the complete result set for batch scopes; visibly select the current page.
        self.ws.all_filtered_selection = set(self.filtered_ids)
        ids = self.app.tree.get_children()
        self.app.tree.selection_set(ids)
        self.app._v3_selection_changed()
        self.app.status.set(f'已选择当前筛选结果中的全部 {len(self.filtered_ids)} 项素材')

    def refresh_categories(self):
        panel = getattr(self.app, 'folder_tree_panel', None)
        if panel is None or not panel.winfo_exists():
            return
        groups = dict(self.app.output_directories())
        base = Path(self.app.out.get() or '.')
        for name in self.app.folder_names():
            target = str(base / '自定义分类' / name)
            groups.setdefault(target, [])
        panel.set_data(groups)
        panel.favorites = {path for path in groups if Path(path).name in self.favorite_names}
        panel.render()

    def _install_category_actions(self):
        panel = self.app.folder_tree_panel
        panel.canvas.bind('<Button-3>', self.category_menu, add='+')

    def _install_category_creator(self):
        self.app.new_folder_for_selection = self.show_create_category
        button = getattr(self.app.folder_tree_panel, 'add_button', None)
        if button is not None:
            button.configure(command=self.show_create_category)

    def show_create_category(self):
        existing = getattr(self, 'create_dialog', None)
        if existing is not None and existing.winfo_exists():
            existing.lift(); return
        dialog = tk.Toplevel(self.app); self.create_dialog = dialog
        dialog.title('新建分类'); dialog.transient(self.app); dialog.resizable(False, False)
        dialog.configure(bg=COLORS['border']); dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)
        body = tk.Frame(dialog, bg='white', padx=22, pady=20); body.pack(fill='both', expand=True, padx=1, pady=1)
        tk.Label(body, text='新建分类', bg='white', fg=COLORS['text'],
                 font=('Segoe UI Semibold', 14)).pack(anchor='w')
        tk.Label(body, text='分类仅保存整理信息，不会修改或移动原始文件。', bg='white',
                 fg=COLORS['muted'], font=('Segoe UI', 9)).pack(anchor='w', pady=(4, 14))
        value = tk.StringVar(); error = tk.StringVar()
        entry_box = tk.Frame(body, bg='white', highlightthickness=1, highlightbackground=COLORS['border'])
        entry_box.pack(fill='x'); entry = tk.Entry(entry_box, textvariable=value, relief='flat', bd=0,
                                                   font=('Segoe UI', 10), fg=COLORS['text'])
        entry.pack(fill='x', padx=12, ipady=10)
        tk.Label(body, textvariable=error, bg='white', fg=COLORS.get('danger', '#D94B45'),
                 font=('Segoe UI', 8)).pack(anchor='w', pady=(5, 0))
        selected = self.ws._selected_indices()
        assign = tk.BooleanVar(value=bool(selected))
        check = tk.Checkbutton(body, text=f'创建后放入当前选中的 {len(selected)} 项素材', variable=assign,
                               bg='white', fg=COLORS['text'], activebackground='white',
                               state='normal' if selected else 'disabled', font=('Segoe UI', 9))
        check.pack(anchor='w', pady=(12, 16))
        buttons = tk.Frame(body, bg='white'); buttons.pack(fill='x')
        def create():
            name = valid_folder_name(value.get())
            if not name:
                error.set('请输入有效名称，且不要包含 \\ / : * ? " < > |'); entry.focus_set(); return
            if name in self.app.folder_names():
                error.set('已存在同名分类，请更换名称。'); entry.focus_set(); return
            catalog_before = list(load_project_folders(self.app.sources))
            favorite_before = list(self.favorite_names)
            add_project_folder(self.app.sources, name)
            action = self.app.workspace_completion_v48._snapshot(selected if assign.get() else [], f'新建分类：{name}')
            action['catalog_before'] = catalog_before
            action['favorite_before'] = favorite_before
            self.ws.undo_stack.append(action)
            if assign.get() and selected:
                self.app.assign_rows([self.app.rows[i] for i in selected], name)
                self.app.status.set(f'已新建“{name}”，并放入 {len(selected)} 项素材 · 可撤销')
            else:
                self.app.render(); self.app.status.set(f'已新建分类“{name}” · 可撤销')
            dialog.destroy(); self.refresh_categories()
        CanvasButton(buttons, '取消', width=104, height=40, command=dialog.destroy).pack(side='right')
        CanvasButton(buttons, '创建分类', variant='primary', width=120, height=40,
                     command=create).pack(side='right', padx=(0, 10))
        entry.bind('<Return>', lambda _e: create()); entry.bind('<Escape>', lambda _e: dialog.destroy())
        dialog.update_idletasks()
        x = self.app.winfo_rootx() + max(0, (self.app.winfo_width()-dialog.winfo_reqwidth())//2)
        y = self.app.winfo_rooty() + max(0, (self.app.winfo_height()-dialog.winfo_reqheight())//2)
        dialog.geometry(f'{max(420, dialog.winfo_reqwidth())}x{dialog.winfo_reqheight()}+{x}+{y}')
        dialog.grab_set(); entry.focus_set()

    def _category_at(self, event):
        panel = self.app.folder_tree_panel
        item = panel._at(event.y)
        if not item or item['key'][0] != 'folder':
            return None
        path = item.get('target') or item.get('path') or ''
        parts = Path(path).parts
        if '自定义分类' not in parts:
            return None
        return item, parts[-1]

    def category_menu(self, event):
        found = self._category_at(event)
        if not found:
            return
        item, name = found
        self.category_menu_at(item, event.x_root, event.y_root)

    def category_menu_at(self, item, x_root, y_root):
        path = item.get('target') or item.get('path') or ''
        name = Path(path).name
        actions = [
            (f'重命名“{name}”', lambda: self.rename_category(name), True, 'normal'),
            ('合并到其他分类', lambda: self.merge_category(name), len(self.app.folder_names()) > 1, 'normal'),
            ('清空分类', lambda: self.clear_category(name), item['count'] > 0, 'normal'),
            ('取消收藏' if name in self.favorite_names else '收藏分类',
             lambda: self.toggle_favorite(name), True, 'normal'),
            ('删除分类', lambda: self.delete_category(name), True, 'danger'),
        ]
        if hasattr(self.app, '_show_context_actions'):
            self.app._show_context_actions(actions, x_root, y_root)
        else:
            anchor = tk.Frame(self.app, width=1, height=1, bg=self.app.cget('bg'))
            anchor.place(x=max(0, x_root-self.app.winfo_rootx()), y=max(0, y_root-self.app.winfo_rooty()))
            anchor.update_idletasks()
            self.app._popup_actions([(label, command, enabled) for label, command, enabled, _ in actions], anchor)
            self._cleanup_popup_anchor(anchor)

    def _cleanup_popup_anchor(self, anchor):
        popup = getattr(self.app, 'active_popup', None)
        if popup is not None and popup.winfo_exists():
            self.app.after(250, lambda: self._cleanup_popup_anchor(anchor))
        elif anchor.winfo_exists():
            anchor.destroy()

    def rename_category(self, old):
        new = valid_folder_name(simpledialog.askstring('重命名分类', '新的分类名称：',
                                                       initialvalue=old, parent=self.app))
        if not new or new == old:
            return
        if new in self.app.folder_names():
            return messagebox.showwarning('名称重复', '已经存在同名分类。', parent=self.app)
        indices = [self.app.rows.index(row) for row in self._rows_in(old)]
        action = self.app.workspace_completion_v48._snapshot(indices, f'重命名分类：{old} → {new}')
        action['catalog_before'] = list(load_project_folders(self.app.sources))
        action['favorite_before'] = list(self.favorite_names)
        self.ws.undo_stack.append(action)
        rename_project_folder(self.app.sources, old, new)
        changed = set()
        for row in self._rows_in(old):
            row['custom_folder'] = new
            changed.add(str(row['p']))
        if changed:
            save_material_folders(self.app.rows, changed)
        if old in self.favorite_names:
            self.favorite_names.discard(old); self.favorite_names.add(new); self._save_favorites()
        self.app.render(); self.app.status.set(f'已将“{old}”重命名为“{new}” · 可撤销')
        self.refresh_categories()

    def _rows_in(self, name):
        return [row for row in self.app.rows if row.get('custom_folder') == name]

    def clear_category(self, name, quiet=False):
        rows = self._rows_in(name)
        if not rows:
            return
        if not quiet and not messagebox.askyesno('清空分类',
                f'将 {len(rows)} 项素材移至未分类吗？\n\n不会删除任何原始文件。', parent=self.app):
            return
        indices = [self.app.rows.index(row) for row in rows]
        self.ws.undo_stack.append(self.app.workspace_completion_v48._snapshot(indices, f'清空分类：{name}'))
        changed = set()
        for row in rows:
            row['custom_folder'] = ''; changed.add(str(row['p']))
        save_material_folders(self.app.rows, changed)
        self.app.render(); self.app.status.set(f'已清空“{name}”中的 {len(rows)} 项素材 · 可撤销')

    def delete_category(self, name):
        rows = self._rows_in(name)
        prompt = f'删除分类“{name}”吗？'
        if rows:
            prompt += f'\n\n其中 {len(rows)} 项素材将移至未分类，原始文件不会被删除。'
        if not messagebox.askyesno('删除分类', prompt, parent=self.app):
            return
        catalog_before = list(load_project_folders(self.app.sources))
        indices = [self.app.rows.index(row) for row in rows]
        action = self.app.workspace_completion_v48._snapshot(indices, f'删除分类：{name}')
        action['catalog_before'] = catalog_before
        action['favorite_before'] = list(self.favorite_names)
        self.ws.undo_stack.append(action)
        if rows:
            changed = set()
            for row in rows:
                row['custom_folder'] = ''
                changed.add(str(row['p']))
            save_material_folders(self.app.rows, changed)
        names = set(load_project_folders(self.app.sources)); names.discard(name)
        save_project_folders(self.app.sources, names)
        self.favorite_names.discard(name); self._save_favorites()
        self.refresh_categories(); self.app.status.set(f'已删除分类“{name}”')

    def merge_category(self, source):
        choices = [name for name in self.app.folder_names() if name != source]
        target = valid_folder_name(simpledialog.askstring('合并分类',
            f'输入目标分类名称：\n可选：{"、".join(choices)}', parent=self.app))
        if not target or target not in choices:
            return messagebox.showwarning('目标分类无效', '请选择一个现有的其他分类。', parent=self.app)
        rows = self._rows_in(source)
        indices = [self.app.rows.index(row) for row in rows]
        action = self.app.workspace_completion_v48._snapshot(indices, f'合并分类：{source} → {target}')
        action['catalog_before'] = list(load_project_folders(self.app.sources))
        action['favorite_before'] = list(self.favorite_names)
        self.ws.undo_stack.append(action)
        self.app.assign_rows(rows, target)
        names = set(load_project_folders(self.app.sources)); names.discard(source)
        save_project_folders(self.app.sources, names)
        self.favorite_names.discard(source); self._save_favorites()
        self.app.render(); self.app.status.set(f'已将“{source}”合并到“{target}” · 可撤销')

    def toggle_favorite(self, name):
        if name in self.favorite_names:
            self.favorite_names.discard(name)
        else:
            self.favorite_names.add(name)
        self._save_favorites(); self.refresh_categories()

    def _install_drag(self):
        tree = self.app.tree
        tree.bind('<ButtonPress-1>', self.drag_press, add='+')
        tree.bind('<B1-Motion>', self.drag_motion)
        tree.bind('<ButtonRelease-1>', self.drag_release)

    def drag_press(self, event):
        iid = self.app.tree.identify_row(event.y)
        self.drag_start = (event.x_root, event.y_root) if iid else None
        self.dragging = False; self.drag_target = None

    def drag_motion(self, event):
        if not self.drag_start or not self.app.tree.selection():
            return
        dx = event.x_root - self.drag_start[0]; dy = event.y_root - self.drag_start[1]
        if not self.dragging and dx * dx + dy * dy < 64:
            return
        self.dragging = True; self.app.tree.configure(cursor='hand2')
        panel = self.app.folder_tree_panel; canvas = panel.canvas
        x = event.x_root - canvas.winfo_rootx(); y = event.y_root - canvas.winfo_rooty()
        item = panel._at(y) if 0 <= x <= canvas.winfo_width() and 0 <= y <= canvas.winfo_height() else None
        valid = bool(item and item['key'][0] == 'folder' and '自定义分类' in Path(item.get('target') or item.get('path') or '').parts)
        self.drag_target = item if valid else None
        panel.hover_key = item['key'] if valid else None
        panel.drop_key = item['key'] if valid else None
        if valid:
            name = Path(item.get('target') or item.get('path')).name
            panel.selected_text.set(f'松开后移动到“{name}”')
        else:
            panel.selected_text.set('拖动到自定义分类即可移动')
        panel.render()
        self.app.status.set(f'拖动 {len(self.app.tree.selection())} 项素材到目标分类')
        return 'break'

    def drag_release(self, event):
        try:
            if self.dragging and self.drag_target:
                target = Path(self.drag_target.get('target') or self.drag_target.get('path')).name
                indices = self.ws._selected_indices()
                self.ws.undo_stack.append(self.app.workspace_completion_v48._snapshot(indices, f'拖动到分类：{target}'))
                self.app.assign_rows([self.app.rows[i] for i in indices], target)
                self.app.render(); self.app.status.set(f'已拖动 {len(indices)} 项到“{target}” · 可撤销')
        finally:
            self.drag_start = None; self.dragging = False; self.drag_target = None
            self.app.tree.configure(cursor='')
            panel = self.app.folder_tree_panel; panel.hover_key = None; panel.drop_key = None
            panel.selected_text.set('拖动所选素材到左侧分类'); panel.render()
        return 'break'
