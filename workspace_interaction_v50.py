import tkinter as tk
from tkinter import messagebox

from v3_ui_components import COLORS, CanvasButton


class WorkspaceInteractionV50:
    """Fixes smart-filter routing and makes batch review controls fully interactive."""

    OPERATIONS = ('自动通过', '待确认', '明显问题', '忽略提示', '重新分析')
    OPERATION_HELP = {
        '自动通过': '素材无需人工处理；白底正常也归入此状态。',
        '待确认': '置信度不足、轻微曝光或画质较低，需要人工确认。',
        '明显问题': '高置信度检测到严重过曝等明显问题。',
        '忽略提示': '忽略当前警告并按通过处理，不修改原文件。',
        '重新分析': '标记后在下次扫描时重新识别。',
    }
    SCOPES = ('当前选择', '当前相似组', '当前筛选结果')

    def __init__(self, app):
        self.app = app
        self.ws = app.unified_workspace
        self.completion = app.workspace_completion_v48
        self.last_selection = []
        self._install_selection_memory()
        self._install_filter_routing()
        self.completion._batch_content = self._batch_content

    def _install_selection_memory(self):
        def remember(_event=None):
            current = []
            for iid in self.app.tree.selection():
                try:
                    index = int(iid)
                except (TypeError, ValueError):
                    continue
                if 0 <= index < len(self.app.rows):
                    current.append(index)
            if current:
                self.last_selection = current
        self.app.tree.bind('<<TreeviewSelect>>', remember, add='+')
        remember()

    def selected_indices(self):
        current = self.ws._selected_indices()
        if current:
            self.last_selection = current
            return current
        return [i for i in self.last_selection if 0 <= i < len(self.app.rows)]

    def _install_filter_routing(self):
        original = self.app.open_category

        def open_category(category):
            audit_routes = {
                '审核:自动通过': '自动通过',
                '审核:白底正常': '白底正常',
                '标签:白底正常': '白底正常',
                '审核:待确认': '待确认',
                '审核:明显问题': '明显问题',
                '审核:文件异常': '文件异常',
            }
            if category in audit_routes:
                value = audit_routes[category]
                self.ws.select_audit(value)
                self.app.status.set(f'已筛选：{value}')
                return
            if category == '全部':
                self.ws.clear_filters()
                self.app.status.set('已显示全部素材')
                return
            if category in ('照片', '视频'):
                self.ws.select_type(category)
                self.app.status.set(f'已筛选：{category}')
                return
            if isinstance(category, str) and category.startswith('标签:'):
                self.app.status.set(f'已选择分析标签：{category.split(":", 1)[1]}')
                return
            return original(category)

        self.app.open_category = open_category

    def _scope_indices(self, scope):
        selected = self.selected_indices()
        if scope == '当前筛选结果':
            feature = getattr(self.app, 'classification_pagination_v49', None)
            ids = feature.filtered_ids if feature is not None else self.app.tree.get_children()
            return sorted({int(i) for i in ids if str(i).isdigit() and int(i) < len(self.app.rows)})
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

    def _batch_content(self, workspace, body):
        footer = tk.Frame(body, bg='white', highlightthickness=1, highlightbackground=COLORS['border'])
        footer.pack(side='bottom', fill='x')
        content = tk.Frame(body, bg='white')
        content.pack(fill='both', expand=True)
        title = tk.Label(content, text='批量审核', bg='white', fg='#17213C',
                         font=('Segoe UI Semibold', 16))
        title.pack(anchor='w', padx=18, pady=(14, 2))
        operation = tk.StringVar(value='自动通过')
        scope_var = tk.StringVar(value='当前选择')
        summary = tk.StringVar()
        tk.Label(content, textvariable=summary, bg='white', fg=COLORS['muted'],
                 font=('Segoe UI', 9)).pack(anchor='w', padx=18, pady=(0, 4))

        op_section = workspace._section(content, '选择操作')
        op_buttons = {}
        op_grid = tk.Frame(op_section, bg='white'); op_grid.pack(fill='x')
        op_grid.columnconfigure(0, weight=1, uniform='operation')
        op_grid.columnconfigure(1, weight=1, uniform='operation')
        selected_operation = tk.StringVar(value='当前操作：自动通过')
        tk.Label(op_section, textvariable=selected_operation, bg='white', fg=COLORS['blue'],
                 font=('Segoe UI Semibold', 9)).pack(anchor='w', pady=(0, 5))
        operation_help = tk.StringVar(value=self.OPERATION_HELP['自动通过'])
        tk.Label(op_section, textvariable=operation_help, bg='white', fg=COLORS['muted'],
                 justify='left', wraplength=300, font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 6))

        scope_section = workspace._section(content, '应用范围')
        scope_buttons = {}
        preview_section = workspace._section(content, '影响结果预览')
        preview = tk.StringVar()
        tk.Label(preview_section, textvariable=preview, bg='white', fg=COLORS['muted'],
                 justify='left', font=('Segoe UI', 9)).pack(anchor='w')

        def refresh_feedback():
            indices = self._scope_indices(scope_var.get())
            before = {}
            reasons = {}
            for index in indices:
                row = self.app.rows[index]
                status = row.get('audit_status', '待确认')
                before[status] = before.get(status, 0) + 1
                reason = row.get('audit_reason', '尚无详细原因')
                reasons[reason] = reasons.get(reason, 0) + 1
            distribution = '、'.join(f'{key} {value}项' for key, value in before.items()) or '无可处理素材'
            reason_text = '、'.join(f'{key} {value}项' for key, value in list(reasons.items())[:3]) or '无'
            summary.set(f'{scope_var.get()}：{len(indices)} 项素材')
            preview.set(f'将“{operation.get()}”应用到 {len(indices)} 项素材\n原审核结果：{distribution}\n判定原因：{reason_text}\n不会修改或删除原始文件')

        def choose_operation(value):
            operation.set(value); selected_operation.set(f'当前操作：{value}')
            operation_help.set(self.OPERATION_HELP[value])
            for name, button in op_buttons.items():
                button.configure(variant='nav-active' if name == value else 'secondary')
            refresh_feedback()

        for index, text in enumerate(self.OPERATIONS):
            button = CanvasButton(op_grid, text, width=145, height=40,
                                  variant='nav-active' if index == 0 else 'secondary',
                                  command=lambda value=text: choose_operation(value))
            button.grid(row=index // 2, column=index % 2, sticky='ew', padx=(0, 4) if index % 2 == 0 else (4, 0), pady=4)
            op_buttons[text] = button

        def choose_scope(value):
            scope_var.set(value)
            for name, button in scope_buttons.items():
                button.configure(variant='nav-active' if name == value else 'secondary')
            refresh_feedback()

        for index, text in enumerate(self.SCOPES):
            button = CanvasButton(scope_section, text, width=300, height=36,
                                  variant='nav-active' if index == 0 else 'secondary',
                                  command=lambda value=text: choose_scope(value))
            button.pack(fill='x', pady=3); scope_buttons[text] = button

        rules = workspace._section(content, '后续规则')
        same_source = tk.BooleanVar(value=False); reference = tk.BooleanVar(value=False)
        for text, variable in (('以后对该来源目录应用相同判断', same_source),
                               ('将当前组作为白底参考', reference)):
            line = tk.Frame(rules, bg='white', height=34); line.pack(fill='x'); line.pack_propagate(False)
            tk.Checkbutton(line, variable=variable, bg='white', activebackground='white',
                           highlightthickness=0).pack(side='left')
            tk.Label(line, text=text, bg='white', fg=COLORS['text']).pack(side='left')

        feedback = tk.StringVar(value='')
        tk.Label(footer, textvariable=feedback, bg='white', fg='#198754',
                 font=('Segoe UI Semibold', 9)).pack(fill='x', padx=14, pady=(8, 0))
        actions = tk.Frame(footer, bg='white'); actions.pack(fill='x', padx=14, pady=(8, 12))
        CanvasButton(actions, '取消', width=118, height=40,
                     command=self.app.page_state.close_drawer).pack(side='left')

        def apply():
            indices = self._scope_indices(scope_var.get())
            if not indices:
                messagebox.showinfo('批量审核', '当前范围内没有素材。请先选择素材，或改为“当前筛选结果”。', parent=self.app)
                return
            workspace.undo_stack.append(self.completion._snapshot(indices, f'批量审核：{operation.get()}'))
            target = operation.get()
            for index in indices:
                row = self.app.rows[index]
                if target == '重新分析':
                    row['needs_reanalysis'] = True
                elif target == '忽略提示':
                    row['manual_audit'] = '自动通过'
                else:
                    row['manual_audit'] = target
            self.app.render(); self.app.status.set(f'已将 {len(indices)} 项标记为“{target}” · 可撤销')
            feedback.set(f'已应用 {len(indices)} 项，可在主工作台撤销')
            apply_button.configure(text=f'已应用 {len(indices)} 项')
            self.app.after(1800, lambda: apply_button.configure(text='应用调整') if apply_button.winfo_exists() else None)

        apply_button = CanvasButton(actions, '应用调整', variant='primary', width=142, height=40,
                                    command=apply)
        apply_button.pack(side='right')
        refresh_feedback()
