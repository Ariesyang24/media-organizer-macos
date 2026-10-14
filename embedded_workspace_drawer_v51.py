import json
import tkinter as tk
from pathlib import Path

from v3_ui_components import COLORS, CanvasButton, RoundedCard, ToggleSwitch


class EmbeddedWorkspaceDrawerV51:
    WIDTH = 360

    def __init__(self, app):
        self.app = app
        self.ws = app.unified_workspace
        self.state = app.page_state
        self.drawer = None
        self.kind = None
        self.saved_padx = {}
        self.saved_toolbar_pack = []
        self.toolbar_line = None
        self.settings_path = Path(__file__).resolve().parent / 'recognition_settings.json'
        self._init_settings()
        self.state.open_drawer = self.open_drawer
        self.state.close_drawer = self.close_drawer
        self.ws.open_drawer = self.open_drawer
        self.ws._close_drawer = self.close_drawer
        self._wrap_render_colors()

    def _init_settings(self):
        defaults = {'smart': True, 'white_protect': True, 'subject_first': True,
                    'sensitivity': '标准', 'scene_on': False, 'faces_on': False,
                    'video_on': True, 'copy_mode': True, 'show_confidence': True}
        try:
            saved = json.loads(self.settings_path.read_text(encoding='utf-8'))
        except (OSError, ValueError, TypeError):
            saved = {}
        values = {**defaults, **saved}
        self.white_protect = tk.BooleanVar(self.app, value=bool(values['white_protect']))
        self.subject_first = tk.BooleanVar(self.app, value=bool(values['subject_first']))
        self.sensitivity = tk.StringVar(self.app, value=values['sensitivity'] if values['sensitivity'] in ('宽松', '标准', '严格') else '标准')
        self.show_confidence = tk.BooleanVar(self.app, value=bool(values['show_confidence']))
        self.app.smart.set(bool(values['smart'])); self.app.scene_on.set(bool(values['scene_on']))
        self.app.faces_on.set(bool(values['faces_on'])); self.app.video_on.set(bool(values['video_on']))
        self.app.copy_mode.set(bool(values['copy_mode']))
        self.app.white_protect = self.white_protect
        self.app.subject_first = self.subject_first
        self.app.recognition_sensitivity = self.sensitivity
        self.app.show_confidence = self.show_confidence

    def _settings_snapshot(self):
        return {
            'smart': bool(self.app.smart.get()), 'white_protect': bool(self.white_protect.get()),
            'subject_first': bool(self.subject_first.get()), 'sensitivity': self.sensitivity.get(),
            'scene_on': bool(self.app.scene_on.get()), 'faces_on': bool(self.app.faces_on.get()),
            'video_on': bool(self.app.video_on.get()), 'copy_mode': bool(self.app.copy_mode.get()),
            'show_confidence': bool(self.show_confidence.get()),
        }

    def _apply_snapshot(self, values):
        for name, variable in (
            ('smart', self.app.smart), ('white_protect', self.white_protect),
            ('subject_first', self.subject_first), ('sensitivity', self.sensitivity),
            ('scene_on', self.app.scene_on), ('faces_on', self.app.faces_on),
            ('video_on', self.app.video_on), ('copy_mode', self.app.copy_mode),
            ('show_confidence', self.show_confidence)):
            variable.set(values[name])

    def _save_settings(self):
        values = self._settings_snapshot()
        self.settings_path.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding='utf-8')
        self.app.status.set('识别设置已保存，新规则将用于审核结果')
        self.app.render()
        self.close_drawer()

    def _cancel_settings(self):
        if hasattr(self, '_open_settings_snapshot'):
            self._apply_snapshot(self._open_settings_snapshot)
        self.close_drawer()

    def restore_defaults(self):
        self.app.smart.set(True); self.white_protect.set(True); self.subject_first.set(True)
        self.sensitivity.set('标准'); self.app.scene_on.set(False); self.app.faces_on.set(False)
        self.app.video_on.set(True); self.app.copy_mode.set(True); self.show_confidence.set(True)
        self.app.status.set('已恢复默认识别设置，点击“保存设置”后生效')

    def _root(self):
        return self.app.v3_recognition_root

    def _reserve_space(self):
        root = self._root()
        width = self.WIDTH if root.winfo_width() >= 1050 else 340
        for child in root.winfo_children():
            if child.winfo_manager() != 'pack':
                continue
            if child not in self.saved_padx:
                self.saved_padx[child] = child.pack_info().get('padx', 0)
            child.pack_configure(padx=(0, width + 10))
        return width

    def _restore_space(self):
        for child, padx in list(self.saved_padx.items()):
            try:
                if child.winfo_exists() and child.winfo_manager() == 'pack':
                    child.pack_configure(padx=padx)
            except tk.TclError:
                pass
        self.saved_padx.clear()

    def _compact_toolbar(self):
        toolbar = getattr(self.ws, 'toolbar', None)
        if toolbar is None or not toolbar.winfo_exists():
            return
        lines = toolbar.pack_slaves()
        if not lines:
            return
        line = lines[0]
        hidden = {'智能审核', '相似项分组', '移动到分类', '识别设置'}
        self.toolbar_line = line
        self.saved_toolbar_pack = [(child, child.pack_info()) for child in line.pack_slaves()]
        for child, _info in self.saved_toolbar_pack:
            try:
                label = child.cget('text')
            except tk.TclError:
                label = ''
            if label in hidden:
                child.pack_forget()

    def _restore_toolbar(self):
        if self.toolbar_line is not None:
            for child in self.toolbar_line.pack_slaves():
                child.pack_forget()
        for child, info in self.saved_toolbar_pack:
            try:
                if child.winfo_exists():
                    info = dict(info); info.pop('in', None)
                    child.pack(**info)
            except tk.TclError:
                pass
        self.saved_toolbar_pack = []
        self.toolbar_line = None

    def close_drawer(self):
        if self.drawer is not None:
            try:
                self.drawer.destroy()
            except tk.TclError:
                pass
        self.drawer = None; self.kind = None
        self.state.drawer = None
        self._restore_space()
        self._restore_toolbar()

    def open_drawer(self, kind='识别设置'):
        self.close_drawer()
        root = self._root(); root.update_idletasks(); width = self._reserve_space()
        self._compact_toolbar()
        drawer = tk.Frame(root, bg=COLORS['border'], width=width)
        drawer.place(relx=1.0, x=0, y=0, anchor='ne', width=width, relheight=1.0)
        drawer.pack_propagate(False)
        shell = tk.Frame(drawer, bg='white'); shell.pack(fill='both', expand=True, padx=1, pady=1)
        self.drawer = drawer; self.kind = kind; self.state.drawer = drawer
        if hasattr(self.state, 'drawer_tab'):
            self.state.drawer_tab.set(kind)
        self._tabs(shell, kind)
        if kind == '识别设置':
            self._open_settings_snapshot = self._settings_snapshot()
            self._settings(shell)
        elif kind == '批量操作':
            self.ws._batch_content(shell)
        else:
            self._details(shell)
        drawer.lift()

    def _tabs(self, shell, active):
        tabs = tk.Frame(shell, bg='white'); tabs.pack(fill='x', padx=12, pady=(12, 7))
        for column in range(3):
            tabs.columnconfigure(column, weight=1, uniform='tabs')
        for column, name in enumerate(('识别设置', '批量操作', '素材详情')):
            def switch(value=name):
                if active == '识别设置' and value != '识别设置':
                    self._cancel_settings()
                self.open_drawer(value)
            button = CanvasButton(tabs, name, width=92, height=38,
                                  variant='nav-active' if name == active else 'secondary',
                                  command=switch)
            button.grid(row=0, column=column, sticky='ew', padx=(0, 4) if column < 2 else 0)
        CanvasButton(tabs, '', icon='close', width=38, height=38,
                     command=self._cancel_settings if active == '识别设置' else self.close_drawer).grid(row=0, column=3, padx=(8, 0))

    def _scroll_body(self, shell):
        canvas = tk.Canvas(shell, bg='white', highlightthickness=0)
        bar = tk.Scrollbar(shell, orient='vertical', command=canvas.yview, width=8)
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(side='left', fill='both', expand=True); bar.pack(side='right', fill='y')
        body = tk.Frame(canvas, bg='white'); window = canvas.create_window(0, 0, anchor='nw', window=body)
        body.bind('<Configure>', lambda _e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: canvas.itemconfigure(window, width=e.width))
        canvas.bind('<MouseWheel>', lambda e: canvas.yview_scroll(-1 if e.delta > 0 else 1, 'units'))
        return body

    def _card(self, parent, title):
        card = tk.Frame(parent, bg='white', highlightthickness=1, highlightbackground=COLORS['border'])
        card.pack(fill='x', padx=12, pady=5)
        tk.Label(card, text=title, bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 10)).pack(anchor='w', padx=12, pady=(10, 5))
        return card

    def _setting_row(self, parent, text, variable, help_text=''):
        row = tk.Frame(parent, bg='white', height=44); row.pack(fill='x', padx=12); row.pack_propagate(False)
        labels = tk.Frame(row, bg='white'); labels.pack(side='left', fill='both', expand=True)
        tk.Label(labels, text=text, bg='white', fg=COLORS['text'], font=('Segoe UI', 9)).pack(anchor='w', pady=(4, 0))
        if help_text:
            tk.Label(labels, text=help_text, bg='white', fg=COLORS['muted'], font=('Segoe UI', 7)).pack(anchor='w')
        ToggleSwitch(row, variable).pack(side='right', pady=8)

    def _settings(self, shell):
        footer = tk.Frame(shell, bg='white', highlightthickness=1, highlightbackground=COLORS['border'])
        footer.pack(side='bottom', fill='x')
        CanvasButton(footer, '取消', width=132, height=40, command=self._cancel_settings).pack(side='left', padx=12, pady=10)
        CanvasButton(footer, '保存设置', variant='primary', width=142, height=40,
                     command=self._save_settings).pack(side='right', padx=12, pady=10)
        body = self._scroll_body(shell)
        head = tk.Frame(body, bg='white'); head.pack(fill='x', padx=14, pady=(5, 6))
        tk.Label(head, text='识别设置', bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 16)).pack(anchor='w')
        tk.Label(head, text='设置识别、视频分析与文件安全', bg='white', fg=COLORS['muted'],
                 font=('Segoe UI', 9)).pack(anchor='w', pady=(2, 0))
        tk.Label(head, text='修改后下次扫描生效', bg='#FFF4DD', fg='#9A6818',
                 padx=8, pady=5, font=('Segoe UI', 8)).pack(anchor='e', pady=(5, 0))

        common = self._card(body, '⌄  常用识别')
        self._setting_row(common, '画质、重复、连拍识别', self.app.smart)
        self._setting_row(common, '白底商品图保护', self.white_protect)
        self._setting_row(common, '主体优先判断', self.subject_first)
        sensitivity = tk.Frame(common, bg='white'); sensitivity.pack(fill='x', padx=12, pady=(5, 10))
        tk.Label(sensitivity, text='识别敏感度', bg='white', fg=COLORS['text'], font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 5))
        choices = tk.Frame(sensitivity, bg='white'); choices.pack(fill='x')
        sensitivity_buttons = {}
        def choose(value):
            self.sensitivity.set(value)
            for key, button in sensitivity_buttons.items(): button.configure(variant='nav-active' if key == value else 'secondary')
        for col, text in enumerate(('宽松', '标准', '严格')):
            choices.columnconfigure(col, weight=1, uniform='sense')
            button = CanvasButton(choices, text, width=88, height=36,
                                  variant='nav-active' if text == self.sensitivity.get() else 'secondary',
                                  command=lambda value=text: choose(value))
            button.grid(row=0, column=col, sticky='ew', padx=2); sensitivity_buttons[text] = button

        classification = self._card(body, '⌄  分类识别')
        self._setting_row(classification, '场景识别并分类', self.app.scene_on)
        self._setting_row(classification, '模特识别并分类', self.app.faces_on)
        CanvasButton(classification, '模特分类管理', icon='settings', width=286, height=40,
                     command=getattr(self.app, 'open_people_manager', lambda: None)).pack(fill='x', padx=12, pady=(4, 10))

        video = self._card(body, '⌄  视频分析')
        self._setting_row(video, '视频镜头、关键帧、画质分析', self.app.video_on)
        safe = self._card(body, '⌄  文件安全')
        self._setting_row(safe, '复制并保留原文件', self.app.copy_mode, '推荐开启，不修改或删除源文件')

        interface = self._card(body, '⌄  界面与导出')
        CanvasButton(interface, '导出审核报告', icon='export', width=286, height=40,
                     command=self.ws.export_review_report).pack(fill='x', padx=12, pady=4)
        CanvasButton(interface, '表格列设置', icon='columns', width=286, height=40,
                     command=self.app._show_column_settings).pack(fill='x', padx=12, pady=4)
        self._setting_row(interface, '显示分析置信度', self.show_confidence)
        CanvasButton(interface, '恢复默认设置', icon='rescan', width=286, height=40,
                     command=self.restore_defaults).pack(fill='x', padx=12, pady=(4, 10))

    def _details(self, shell):
        body = tk.Frame(shell, bg='white'); body.pack(fill='both', expand=True, padx=14, pady=8)
        tk.Label(body, text='素材详情', bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 16)).pack(anchor='w', pady=(5, 10))
        selected = self.ws._selected_indices()
        if not selected:
            tk.Label(body, text='请先在表格中选择一个素材', bg='white', fg=COLORS['muted']).pack(pady=50)
            return
        row = self.app.rows[selected[0]]; card = self._card(body, '当前素材')
        details = (('文件名', row['p'].name), ('类型', row.get('kind', '')),
                   ('分析结果', row.get('audit_result', '未分析')), ('置信度', f"{row.get('audit_confidence', 0)}%"),
                   ('审核状态', row.get('audit_status', '待确认')), ('当前分类', row.get('custom_folder') or '未分类'),
                   ('原文件路径', str(row['p'])))
        for label, value in details:
            line = tk.Frame(card, bg='white'); line.pack(fill='x', padx=12, pady=5)
            tk.Label(line, text=label, width=8, anchor='w', bg='white', fg=COLORS['muted']).pack(side='left')
            tk.Label(line, text=value, anchor='w', justify='left', wraplength=205,
                     bg='white', fg=COLORS['text']).pack(side='left', fill='x', expand=True)
        actions = tk.Frame(body, bg='white'); actions.pack(fill='x', pady=10)
        CanvasButton(actions, '打开原文件', width=142, height=40,
                     command=self.app.open_original).pack(side='left')
        CanvasButton(actions, '视频关键帧', width=142, height=40,
                     command=self.app.open_keyframes).pack(side='right')

    def _wrap_render_colors(self):
        original = self.app.render
        def render():
            original(); self.app.after_idle(self.apply_row_colors)
        self.app.render = render
        self.apply_row_colors()

    def apply_row_colors(self):
        tree = self.app.tree
        palette = {'自动通过': '#F1FAF6', '待确认': '#FFF8E8',
                   '明显问题': '#FFF0EF', '文件异常': '#FFECEC'}
        for status, color in palette.items():
            tree.tag_configure('audit_' + status, background=color)
        for index, row in enumerate(self.app.rows):
            iid = str(index)
            if not tree.exists(iid):
                continue
            status = row.get('audit_status', '待确认')
            tree.item(iid, tags=('audit_' + status,))
