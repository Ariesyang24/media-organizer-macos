import tkinter as tk
from types import MethodType
from tkinter import messagebox

from v3_ui_components import COLORS, CanvasButton, RoundedCard


class WorkspaceCompletionV48:
    """Completes the P0 audit, batch and classification interactions."""

    def __init__(self, app):
        self.app = app
        self.ws = app.unified_workspace
        self.ws._batch_content = lambda body: self._batch_content(self.ws, body)
        self.ws._category_content = lambda body: self._category_content(self.ws, body)
        self.ws.undo = lambda: self.undo(self.ws)
        self.ws.show_more_menu = lambda: self.show_more_menu(self.ws)
        self.ws.restore_selected_analysis = lambda: self.restore_selected_analysis(self.ws)
        self.ws.reanalyse_selected = lambda: self.reanalyse_selected(self.ws)
        original_open_drawer = app.page_state.open_drawer
        def open_drawer(kind='识别设置'):
            original_open_drawer(kind)
            self._wire_drawer_actions(kind)
        app.page_state.open_drawer = open_drawer
        self.ws.open_drawer = open_drawer
        original_refresh = self.ws.refresh

        def refresh(workspace):
            original_refresh()
            self.render_filter_chips()

        self.ws.refresh = MethodType(refresh, self.ws)
        self.render_filter_chips()

    def _indices(self, workspace, scope):
        selected = workspace._selected_indices()
        if scope == '当前筛选结果':
            return sorted({int(i) for i in self.app.tree.get_children() if str(i).isdigit()})
        if scope == '当前相似组':
            if not selected:
                return []
            row = self.app.rows[selected[0]]
            group = row.get('duplicate') or row.get('burst')
            if not group:
                return selected
            return [i for i, item in enumerate(self.app.rows)
                    if item.get('duplicate') == group or item.get('burst') == group]
        return selected

    def _snapshot(self, indices, operation):
        rows = {}
        for index in indices:
            row = self.app.rows[index]
            rows[index] = {
                'manual_audit': row.get('manual_audit'),
                'white_background': bool((row.get('analysis') or {}).get('white_background')),
                'custom_folder': row.get('custom_folder', ''),
                'excluded': bool(row.get('excluded', False)),
            }
        return {'operation': operation, 'rows': rows}

    def _batch_content(self, workspace, body):
        selected = workspace._selected_indices()
        tk.Label(body, text='批量审核', bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 16)).pack(anchor='w', padx=18, pady=(14, 2))
        count_var = tk.StringVar(value=f'当前选择 {len(selected)} 项素材')
        tk.Label(body, textvariable=count_var, bg='white', fg=COLORS['muted']).pack(anchor='w', padx=18)

        operation = tk.StringVar(value='白底正常')
        section = workspace._section(body, '选择操作')
        op_buttons = {}
        for text in ('白底正常', '自动通过', '待确认', '明显问题', '忽略提示', '重新分析'):
            def choose(value=text):
                operation.set(value)
                for name, button in op_buttons.items():
                    button.configure(variant='nav-active' if name == value else 'secondary')
            button = CanvasButton(section, text, width=145, height=36,
                                  variant='nav-active' if text == operation.get() else 'secondary',
                                  command=choose)
            button.pack(side='left' if len(op_buttons) % 2 == 0 else 'right', pady=3)
            op_buttons[text] = button

        scope_var = tk.StringVar(value='当前选择')
        scope = workspace._section(body, '应用范围')
        for text in ('当前选择', '当前相似组', '当前筛选结果'):
            row = tk.Frame(scope, bg='white'); row.pack(fill='x', pady=2)
            CanvasButton(row, text, width=300, height=34,
                         command=lambda value=text: (scope_var.set(value),
                             count_var.set(f'{value} {len(self._indices(workspace, value))} 项素材'))).pack(fill='x')

        rules = workspace._section(body, '后续规则')
        same_source = tk.BooleanVar(value=False)
        reference = tk.BooleanVar(value=False)
        for text, variable in (('以后对该来源目录应用相同判断', same_source),
                               ('将当前组作为白底参考', reference)):
            row = tk.Frame(rules, bg='white', height=34); row.pack(fill='x'); row.pack_propagate(False)
            tk.Checkbutton(row, variable=variable, bg='white', activebackground='white',
                           highlightthickness=0).pack(side='left')
            tk.Label(row, text=text, bg='white', fg=COLORS['text']).pack(side='left')

        preview = workspace._section(body, '影响结果预览')
        preview_text = tk.StringVar()
        def update_preview(*_):
            indices = self._indices(workspace, scope_var.get())
            before = {}
            for i in indices:
                value = self.app.rows[i].get('audit_status', '待确认')
                before[value] = before.get(value, 0) + 1
            distribution = '、'.join(f'{key}{value}项' for key, value in before.items()) or '无'
            preview_text.set(f'影响 {len(indices)} 项素材\n原审核结果：{distribution}\n不会修改或删除原始文件')
        tk.Label(preview, textvariable=preview_text, bg='white', fg=COLORS['muted'],
                 justify='left').pack(anchor='w')
        scope_var.trace_add('write', update_preview); operation.trace_add('write', update_preview); update_preview()

        footer = tk.Frame(body, bg='white'); footer.pack(side='bottom', fill='x', padx=14, pady=14)
        CanvasButton(footer, '取消', width=118, height=40,
                     command=self.app.page_state.close_drawer).pack(side='left')
        def apply():
            indices = self._indices(workspace, scope_var.get())
            if not indices:
                return messagebox.showinfo('批量审核', '请先选择需要调整的素材。', parent=self.app)
            workspace.undo_stack.append(self._snapshot(indices, f'批量审核：{operation.get()}'))
            target = operation.get()
            for index in indices:
                row = self.app.rows[index]
                if target == '重新分析':
                    row['needs_reanalysis'] = True
                    continue
                if target == '忽略提示':
                    row['manual_audit'] = '已忽略'
                elif target == '白底正常':
                    row.setdefault('analysis', {})['white_background'] = True
                    row['manual_audit'] = '已人工确认'
                else:
                    row['manual_audit'] = target
            self.app.render()
            self.app.status.set(f'本次已调整 {len(indices)} 项 · 可撤销')
            self.app.page_state.close_drawer()
        CanvasButton(footer, '应用调整', variant='primary', width=142, height=40,
                     command=apply).pack(side='right')

    def _category_content(self, workspace, body):
        selected = workspace._selected_indices()
        tk.Label(body, text='分类调整', bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 16)).pack(anchor='w', padx=18, pady=(14, 2))
        tk.Label(body, text=f'已选择 {len(selected)} 项素材', bg='white',
                 fg=COLORS['muted']).pack(anchor='w', padx=18)

        names = list(self.app.folder_names())
        target = tk.StringVar(value=names[0] if names else '')
        section = workspace._section(body, '目标分类')
        if not names:
            tk.Label(section, text='暂无自定义分类，可先新建分类', bg='white',
                     fg=COLORS['muted']).pack(anchor='w', pady=8)
        for name in names:
            CanvasButton(section, name, icon='folder', width=300, height=36,
                         command=lambda value=name: target.set(value)).pack(fill='x', pady=2)

        scope_var = tk.StringVar(value='当前选择')
        scope = workspace._section(body, '应用范围')
        for text in ('当前选择', '当前相似组', '当前筛选结果'):
            CanvasButton(scope, text, width=300, height=34,
                         command=lambda value=text: scope_var.set(value)).pack(fill='x', pady=2)

        preview = workspace._section(body, '变更预览')
        preview_text = tk.StringVar()
        def update(*_):
            preview_text.set(f'将 {len(self._indices(workspace, scope_var.get()))} 项素材移动到“{target.get() or "未选择"}”\n只修改分类归属，不修改原始文件')
        tk.Label(preview, textvariable=preview_text, bg='white', fg=COLORS['muted'],
                 justify='left').pack(anchor='w')
        target.trace_add('write', update); scope_var.trace_add('write', update); update()

        footer = tk.Frame(body, bg='white'); footer.pack(side='bottom', fill='x', padx=14, pady=14)
        CanvasButton(footer, '新建分类', icon='add', width=126, height=40,
                     command=self.app.new_folder_for_selection).pack(side='left')
        def move():
            indices = self._indices(workspace, scope_var.get())
            if not indices or not target.get():
                return messagebox.showinfo('分类调整', '请选择素材和目标分类。', parent=self.app)
            workspace.undo_stack.append(self._snapshot(indices, f'移动到分类：{target.get()}'))
            self.app.assign_rows([self.app.rows[i] for i in indices], target.get())
            self.app.render(); self.app.status.set(f'已移动 {len(indices)} 项到“{target.get()}” · 可撤销')
            self.app.page_state.close_drawer()
        CanvasButton(footer, '移动所选素材', variant='primary', width=150, height=40,
                     command=move).pack(side='right')

    def undo(self, workspace):
        if not workspace.undo_stack:
            return messagebox.showinfo('撤销', '当前没有可撤销的调整。', parent=self.app)
        action = workspace.undo_stack.pop()
        if isinstance(action, dict) and 'rows' in action:
            for index, old in action['rows'].items():
                if index >= len(self.app.rows):
                    continue
                row = self.app.rows[index]
                if old['manual_audit'] is None:
                    row.pop('manual_audit', None)
                else:
                    row['manual_audit'] = old['manual_audit']
                row.setdefault('analysis', {})['white_background'] = old['white_background']
                row['custom_folder'] = old['custom_folder']
                row['excluded'] = old['excluded']
            self.app.render(); self.app.status.set(f'已撤销：{action["operation"]}')
            return
        # Compatibility with adjustments created by the previous version.
        for index, values in action.items():
            if index < len(self.app.rows):
                status, result = values
                if status is None: self.app.rows[index].pop('manual_audit', None)
                else: self.app.rows[index]['manual_audit'] = status
                self.app.rows[index]['audit_result'] = result
        self.app.render()

    def restore_selected_analysis(self, workspace):
        indices = workspace._selected_indices()
        if not indices:
            return messagebox.showinfo('恢复分析结果', '请先选择素材。', parent=self.app)
        workspace.undo_stack.append(self._snapshot(indices, '恢复分析结果'))
        for index in indices:
            row = self.app.rows[index]
            row.pop('manual_audit', None); row.pop('needs_reanalysis', None)
        self.app.render(); self.app.status.set(f'已恢复 {len(indices)} 项的自动分析结果 · 可撤销')

    def _descendants(self, widget):
        for child in widget.winfo_children():
            yield child
            yield from self._descendants(child)

    def _wire_drawer_actions(self, kind):
        drawer = self.app.page_state.drawer
        if kind != '识别设置' or drawer is None:
            return
        for widget in self._descendants(drawer):
            try:
                if widget.cget('text') == '恢复默认设置':
                    widget.configure(command=self.restore_defaults)
            except (tk.TclError, KeyError):
                pass

    def restore_defaults(self):
        self.app.smart.set(True)
        self.app.scene_on.set(False)
        self.app.faces_on.set(False)
        self.app.video_on.set(True)
        self.app.copy_mode.set(True)
        self.app.status.set('已恢复默认识别设置')

    def reanalyse_selected(self, workspace):
        indices = workspace._selected_indices()
        if not indices:
            return messagebox.showinfo('重新分析', '请先选择素材。', parent=self.app)
        workspace.undo_stack.append(self._snapshot(indices, '重新分析所选素材'))
        for index in indices:
            self.app.rows[index]['needs_reanalysis'] = True
        self.app.status.set(f'已将 {len(indices)} 项标记为重新分析；下次扫描时生效 · 可撤销')
    def show_more_menu(self, workspace):
        selected = bool(self.app.tree.selection())
        self.app._popup_actions([
            ('打开原文件', self.app.open_original, selected),
            ('打开视频关键帧', self.app.open_keyframes, selected),
            ('从整理中移除', self.app.remove_selected_from_plan, selected and not self.app.scan_busy),
            ('重新分析所选素材', workspace.reanalyse_selected, selected and not self.app.scan_busy),
            ('恢复分析结果', workspace.restore_selected_analysis, selected and not self.app.scan_busy),
            ('更改保存位置', self.app._change_output_guarded, not self.app.scan_busy),
        ], workspace.more_btn)

    def render_filter_chips(self):
        workspace = self.ws
        if not hasattr(workspace, 'chips_frame') or not workspace.chips_frame.winfo_exists():
            return
        for widget in list(workspace.chips_frame.winfo_children()):
            widget.destroy()
        active = []
        if workspace.audit_filter != '全部素材':
            active.append(('审核', workspace.audit_filter,
                           lambda: (setattr(workspace, 'audit_filter', '全部素材'), self.app.apply_filter())))
        if workspace.type_filter != '全部类型':
            active.append(('类型', workspace.type_filter,
                           lambda: (setattr(workspace, 'type_filter', '全部类型'), self.app.apply_filter())))
        for _, value, command in active:
            CanvasButton(workspace.chips_frame, value + ' ×', width=max(82, len(value) * 18 + 34),
                         height=30, variant='danger', command=command).pack(side='left', padx=(0, 5))
        shown = len(self.app.tree.get_children())
        workspace.filtered_text = tk.StringVar(value=f'当前筛选 {shown} 项')
        tk.Label(workspace.chips_frame, textvariable=workspace.filtered_text, bg='white',
                 fg=COLORS['muted'], font=('Segoe UI', 8)).pack(side='left', padx=5)
        CanvasButton(workspace.chips_frame, '清空筛选', width=86, height=30,
                     command=workspace.clear_filters).pack(side='left', padx=4)
        CanvasButton(workspace.chips_frame, '撤销', width=72, height=30,
                     command=workspace.undo).pack(side='left', padx=4)
        CanvasButton(workspace.chips_frame, '选择当前筛选结果', width=150, height=30,
                     command=workspace.select_filtered).pack(side='right')
