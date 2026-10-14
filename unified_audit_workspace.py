import csv
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from v3_ui_components import COLORS, CanvasButton, RoundedCard, ToggleSwitch
from svg_icon_system import SvgIcon


AUDIT_ORDER = ('全部素材', '自动通过', '待确认', '明显问题', '文件异常')
AUDIT_ICONS = ('layers', 'check', 'help', 'warning', 'warning')
AUDIT_COLORS = ('#4263EB', '#19A477', '#E7A23B', '#D94B45', '#D94B45')


class UnifiedAuditWorkspace:
    """Presentation/controller layer over the existing, proven scan and organize engine."""

    def __init__(self, app):
        self.app = app
        self.audit_filter = '全部素材'
        self.type_filter = '全部类型'
        self.filter_chips = []
        self.undo_stack = []
        self.drawer = None
        self.drawer_kind = None
        self.audit_values = {name: tk.StringVar(value='0') for name in AUDIT_ORDER}
        app.recognition_settings_button.pack_forget()
        self._replace_toolbar()
        self._configure_review_table()
        self.refresh()

    def enrich(self):
        for row in self.app.rows:
            analysis = row.get('analysis') or {}
            if not analysis:
                result = '等待分析' if self.app.smart.get() else '未启用智能审核'
                status = row.get('manual_audit') or '待确认'
                row['audit_result'] = result
                row['audit_status'] = status
                row['audit_confidence'] = 0
                row['audit_reason'] = '人工指定' if row.get('manual_audit') else '尚未产生可靠的分析结果'
                continue
            valid = analysis.get('valid', True) and row.get('recommend') != '无法解码'
            exposure = str(analysis.get('exposure') or '')
            quality = float(analysis.get('quality') or 0)
            white = bool(analysis.get('white_background'))
            white_protect = bool(getattr(self.app, 'white_protect', tk.BooleanVar(value=True)).get())
            subject_first = bool(getattr(self.app, 'subject_first', tk.BooleanVar(value=True)).get())
            sensitivity = getattr(self.app, 'recognition_sensitivity', tk.StringVar(value='标准')).get()
            quality_limit = {'宽松': 15, '标准': 25, '严格': 40}.get(sensitivity, 25)
            if white and not white_protect:
                exposure = str(analysis.get('raw_exposure') or exposure)
            if not valid:
                result, status, confidence = '文件异常', '文件异常', 100
                reason = '文件无法解码、损坏或格式不受支持'
            elif white and white_protect:
                # The recognition engine verifies a white border plus a detailed foreground.
                # Intentional studio-white backgrounds must not become overexposure failures.
                result, status, confidence = '白底正常', row.get('manual_audit') or '自动通过', 96
                reason = '白色背景符合商品图特征，主体细节保留正常'
            elif '严重' in exposure and subject_first and analysis.get('subject_present'):
                result, status, confidence = exposure, row.get('manual_audit') or '待确认', 76
                reason = f'检测到{exposure}，但主体仍可辨识，需要人工确认'
            elif '严重' in exposure:
                result, status, confidence = exposure, row.get('manual_audit') or '明显问题', 91
                reason = f'高置信度检测到{exposure}'
            elif '轻微' in exposure or quality < quality_limit:
                if sensitivity == '宽松' and '轻微' in exposure and quality >= quality_limit:
                    result, status, confidence = exposure, row.get('manual_audit') or '自动通过', 72
                    reason = f'宽松灵敏度下允许{exposure}'
                else:
                    result, status, confidence = exposure or '画质待核对', row.get('manual_audit') or '待确认', 68
                    reason = (f'检测到{exposure}，当前灵敏度下需要确认'
                              if '轻微' in exposure else f'画质评分低于{quality_limit}，需要人工确认')
            else:
                result, status = ('主体正常' if row.get('kind') == '视频' else '画质正常'), row.get('manual_audit') or '自动通过'
                confidence = max(72, min(99, round(72 + quality * .27)))
                reason = '文件有效，画质和曝光未发现明显问题'
            row['audit_result'] = result
            row['audit_status'] = status
            row['audit_confidence'] = int(confidence)
            row['audit_reason'] = '人工指定' if row.get('manual_audit') else reason

    def _install_audit_strip(self):
        root = self.app.v3_recognition_root
        children = root.pack_slaves()
        content = children[-1]
        strip = tk.Frame(root, bg=COLORS['app_bg'])
        strip.pack(fill='x', pady=(0, 10), before=content)
        tk.Label(strip, text='智能审核', bg=COLORS['app_bg'], fg='#17213C',
                 font=('Segoe UI Semibold', 12)).pack(side='left', padx=(0, 10))
        for name, icon, color in zip(AUDIT_ORDER, AUDIT_ICONS, AUDIT_COLORS):
            card = RoundedCard(strip, height=66, padding=8)
            card.pack(side='left', fill='x', expand=True, padx=4)
            row = tk.Frame(card.body, bg='white', cursor='hand2'); row.pack(fill='both', expand=True)
            SvgIcon(row, icon, color, 'white', size=34, icon_size=21).pack(side='left', padx=(0, 5))
            labels = tk.Frame(row, bg='white'); labels.pack(side='left', fill='both', expand=True)
            tk.Label(labels, text=name, bg='white', fg=COLORS['muted'], font=('Segoe UI', 8)).pack(anchor='w')
            tk.Label(labels, textvariable=self.audit_values[name], bg='white', fg='#17213C',
                     font=('Segoe UI Semibold', 13)).pack(anchor='w')
            for widget in (card, card.body, row, labels):
                widget.bind('<ButtonRelease-1>', lambda _e, value=name: self.select_audit(value), add='+')
        self.audit_strip = strip

    def _right_body(self):
        root = self.app.v3_recognition_root
        content = root.pack_slaves()[-1]
        right_card = content.pack_slaves()[-1]
        return right_card.body

    def _replace_toolbar(self):
        rb = self._right_body()
        widgets = rb.pack_slaves()
        toolbar = widgets[1]
        for child in toolbar.winfo_children(): child.destroy()
        line = tk.Frame(toolbar, bg='white'); line.pack(fill='x')
        self.type_btn = CanvasButton(line, '全部类型', icon='filter', width=104, height=38,
                                     command=self.show_type_menu); self.type_btn.pack(side='left', padx=(0, 4))
        self.audit_btn = CanvasButton(line, '审核状态', icon='check', width=108, height=38,
                                      command=self.show_audit_menu); self.audit_btn.pack(side='left', padx=4)
        CanvasButton(line, '智能审核', icon='smart', width=108, height=38,
                     command=lambda: self.open_drawer('批量操作')).pack(side='left', padx=4)
        CanvasButton(line, '相似项分组', icon='duplicate', width=116, height=38,
                     command=self.select_similar_group).pack(side='left', padx=4)
        CanvasButton(line, '批量调整', icon='batch', width=106, height=38,
                     command=lambda: self.open_drawer('批量操作')).pack(side='left', padx=4)
        CanvasButton(line, '移动到分类', icon='folder', width=122, height=38,
                     command=lambda: self.open_drawer('分类管理')).pack(side='left', padx=4)
        CanvasButton(line, '识别设置', icon='settings', width=106, height=38,
                     command=lambda: self.open_drawer('识别设置')).pack(side='left', padx=4)
        self.more_btn = CanvasButton(line, '', icon='more', width=40, height=38,
                                     command=self.show_more_menu); self.more_btn.pack(side='left', padx=4)
        self.execute_btn = CanvasButton(line, '执行整理', icon='organize', variant='primary', width=112,
                                        height=38, command=self.execute_summary)
        self.execute_btn.pack(side='right')
        chips = tk.Frame(toolbar, bg='white'); chips.pack(fill='x', pady=(6, 0))
        self.chips_frame = chips
        self.filtered_text = tk.StringVar(value='当前筛选 0 项')
        tk.Label(chips, textvariable=self.filtered_text, bg='white', fg=COLORS['muted'], font=('Segoe UI', 8)).pack(side='left', padx=4)
        self.clear_btn = CanvasButton(chips, '清空筛选', width=86, height=30, command=self.clear_filters)
        self.clear_btn.pack(side='left', padx=4)
        self.undo_btn = CanvasButton(chips, '撤销上一步', icon='rescan', width=104, height=30, command=self.undo)
        self.undo_btn.pack(side='left', padx=4)
        CanvasButton(chips, '选择当前筛选结果', width=150, height=30,
                     command=self.select_filtered).pack(side='right')
        self.toolbar = toolbar

    def _configure_review_table(self):
        tree = self.app.tree
        headings = {'#0':'预览','file':'文件名','kind':'类型','quality':'分析结果',
                    'duplicate':'置信度','recommend':'审核状态','target':'当前分类','video':'操作'}
        for col, text in headings.items():
            try: tree.heading(col, text=text, anchor='center')
            except tk.TclError: pass
        desired = ['file','kind','quality','duplicate','recommend','target','video']
        if hasattr(self.app, 'show_confidence') and not self.app.show_confidence.get():
            desired.remove('duplicate')
        display = tuple(c for c in desired if c in tree['columns'])
        tree.configure(displaycolumns=display)
        widths = {'#0':86,'file':220,'kind':76,'quality':110,'duplicate':78,'recommend':105,'target':130,'video':56}
        for col, width in widths.items():
            try: tree.column(col, width=width, minwidth=50, stretch=col == 'file', anchor='center')
            except tk.TclError: pass

    def refresh(self):
        self.enrich()
        counts = {name: 0 for name in AUDIT_ORDER}; counts['全部素材'] = len(self.app.rows)
        for row in self.app.rows:
            status = row.get('audit_status', '待确认')
            if status in counts: counts[status] += 1
        for key, variable in self.audit_values.items(): variable.set(str(counts[key]))
        for index, row in enumerate(self.app.rows):
            iid = str(index)
            if not self.app.tree.exists(iid): continue
            category = row.get('custom_folder') or '未分类'
            for col, value in (('quality', row.get('audit_result','未分析')),
                               ('duplicate', f"{row.get('audit_confidence',0)}%"),
                               ('recommend', row.get('audit_status','待确认')),
                               ('target', category), ('video', '…')):
                if col in self.app.tree['columns']: self.app.tree.set(iid, col, value)
        shown = len(self.app.tree.get_children())
        self.filtered_text.set(f'当前筛选 {shown} 项')
        self._configure_review_table()
        if hasattr(self.app, 'folder_tree_panel'):
            self.app.folder_tree_panel.render()

    def matches(self, row):
        if self.type_filter == '照片' and row.get('kind') != '照片': return False
        if self.type_filter == '视频' and row.get('kind') != '视频': return False
        if self.type_filter == '文件异常' and row.get('audit_status') != '文件异常': return False
        if self.audit_filter != '全部素材':
            if self.audit_filter == '白底正常':
                if row.get('audit_result') != '白底正常': return False
            elif row.get('audit_status') != self.audit_filter: return False
        text = self.app.search_var.get().strip().lower()
        return not text or text in ' '.join((row['p'].name, row.get('dev',''), row.get('place',''), row.get('audit_result',''))).lower()

    def select_audit(self, value):
        self.audit_filter = value; self.audit_btn.configure(text=value if value != '全部素材' else '审核状态')
        self.app.apply_filter()

    def select_type(self, value):
        self.type_filter = value; self.type_btn.configure(text=value); self.app.apply_filter()

    def clear_filters(self):
        self.audit_filter = '全部素材'; self.type_filter = '全部类型'
        self.type_btn.configure(text='全部类型'); self.audit_btn.configure(text='审核状态'); self.app.apply_filter()

    def show_type_menu(self):
        self.app._popup_actions([(v, lambda x=v: self.select_type(x), True) for v in ('全部类型','照片','视频','文件异常')], self.type_btn)

    def show_audit_menu(self):
        self.app._popup_actions([(v, lambda x=v: self.select_audit(x), True) for v in AUDIT_ORDER], self.audit_btn)

    def show_more_menu(self):
        selected = bool(self.app.tree.selection())
        self.app._popup_actions([
            ('打开原文件', self.app.open_original, selected),
            ('打开视频关键帧', self.app.open_keyframes, selected),
            ('从整理中移除', self.app.remove_selected_from_plan, selected and not self.app.scan_busy),
            ('重新分析所选素材', self.reanalyse_selected, selected and not self.app.scan_busy),
            ('更改保存位置', self.app._change_output_guarded, not self.app.scan_busy),
            ('返回素材选择', lambda: self.app._select_page(0), True),
        ], self.more_btn)

    def select_filtered(self):
        self.app.tree.selection_set(self.app.tree.get_children())
        self.app._v3_selection_changed()

    def select_similar_group(self):
        selected = self.app.tree.selection()
        if not selected: return messagebox.showinfo('相似项分组','请先选择一个素材。',parent=self.app)
        row = self.app.rows[int(selected[0])]; group = row.get('duplicate') or row.get('burst')
        if not group: return messagebox.showinfo('相似项分组','该素材暂无重复或连拍组。',parent=self.app)
        ids = [str(i) for i,r in enumerate(self.app.rows) if r.get('duplicate') == group or r.get('burst') == group]
        self.app.tree.selection_set(ids)

    def _close_drawer(self):
        if self.drawer is not None:
            try: self.drawer.destroy()
            except tk.TclError: pass
        self.drawer = None; self.drawer_kind = None

    def open_drawer(self, kind):
        if self.drawer is not None and self.drawer.winfo_exists() and self.drawer_kind == kind:
            self._close_drawer(); return
        self._close_drawer(); self.drawer_kind = kind
        d = tk.Toplevel(self.app); self.drawer = d; d.overrideredirect(True); d.transient(self.app); d.configure(bg=COLORS['border'])
        width = 390; height = max(620, self.app.winfo_height()-38)
        x = self.app.winfo_rootx()+self.app.winfo_width()-width-8; y = self.app.winfo_rooty()+30
        d.geometry(f'{width}x{height}+{x}+{y}')
        body = tk.Frame(d,bg='white'); body.pack(fill='both',expand=True,padx=1,pady=1)
        head=tk.Frame(body,bg='white');head.pack(fill='x',padx=18,pady=(16,8))
        tk.Label(head,text=kind,bg='white',fg='#17213C',font=('Segoe UI Semibold',16)).pack(side='left')
        CanvasButton(head,'',icon='close',width=36,height=36,command=self._close_drawer).pack(side='right')
        if kind == '识别设置': self._settings_content(body)
        elif kind == '分类管理': self._category_content(body)
        else: self._batch_content(body)
        d.bind('<Escape>',lambda _e:self._close_drawer());d.lift()

    def _section(self, parent, title):
        card = RoundedCard(parent, padding=12); card.pack(fill='x', padx=14, pady=5)
        tk.Label(card.body,text=title,bg='white',fg='#17213C',font=('Segoe UI Semibold',10)).pack(anchor='w',pady=(0,6))
        return card.body

    def _settings_content(self, body):
        tk.Label(body,text='设置识别、视频分析与文件安全',bg='white',fg=COLORS['muted']).pack(anchor='w',padx=18,pady=(0,8))
        groups=[('常用识别',[('画质、重复、连拍识别',self.app.smart),('白底商品图保护',tk.BooleanVar(value=True))]),
                ('分类识别',[('场景识别并分类',self.app.scene_on),('模特识别并分类',self.app.faces_on)]),
                ('视频分析',[('视频镜头、关键帧、画质分析',self.app.video_on)]),
                ('文件安全',[('复制并保留原文件',self.app.copy_mode)])]
        for title, options in groups:
            section=self._section(body,title)
            for text,var in options:
                row=tk.Frame(section,bg='white');row.pack(fill='x',pady=5);tk.Label(row,text=text,bg='white',fg=COLORS['text']).pack(side='left');ToggleSwitch(row,var,command=self.app._drawer_setting_changed).pack(side='right')
        tk.Label(body,text='修改后将在下次扫描生效',bg='#FFF7E8',fg='#8A5B16',padx=10,pady=8).pack(fill='x',padx=14,pady=8)
        CanvasButton(body,'保存设置',variant='primary',height=42,command=self._close_drawer).pack(fill='x',padx=14,pady=10)

    def _selected_indices(self):
        result=[]
        for iid in self.app.tree.selection():
            try: result.append(int(iid))
            except ValueError: pass
        return [i for i in result if 0 <= i < len(self.app.rows)]

    def _batch_content(self, body):
        indices=self._selected_indices();tk.Label(body,text=f'应用到 {len(indices)} 项素材',bg='white',fg=COLORS['muted']).pack(anchor='w',padx=18)
        section=self._section(body,'选择操作')
        operation=tk.StringVar(value='标记为白底正常')
        for text in ('标记为白底正常','标记为自动通过','标记为待确认','标记为明显问题'):
            CanvasButton(section,text,width=300,height=36,command=lambda v=text:operation.set(v)).pack(fill='x',pady=3)
        scope=self._section(body,'应用范围')
        tk.Label(scope,text='当前选择 / 当前相似组 / 当前筛选结果',bg='white',fg=COLORS['muted'],wraplength=320).pack(anchor='w')
        preview=self._section(body,'影响结果预览')
        tk.Label(preview,text=f'影响 {len(indices)} 项；只更新审核结果与分类信息。\n不会修改或删除原始文件。',bg='white',fg=COLORS['muted'],justify='left').pack(anchor='w')
        buttons=tk.Frame(body,bg='white');buttons.pack(side='bottom',fill='x',padx=14,pady=14)
        CanvasButton(buttons,'取消',width=110,command=self._close_drawer).pack(side='left')
        def apply():
            if not indices:return
            old={i:(self.app.rows[i].get('manual_audit'),self.app.rows[i].get('audit_result')) for i in indices};self.undo_stack.append(old)
            target=operation.get().replace('标记为','')
            for i in indices:
                self.app.rows[i]['manual_audit'] = '自动通过' if target == '白底正常' else target
                if target == '白底正常': self.app.rows[i]['analysis']['white_background']=True
            self.app.render();self._close_drawer();self.app.status.set(f'本次已调整 {len(indices)} 项，执行整理前可撤销')
        CanvasButton(buttons,'应用调整',variant='primary',width=140,command=apply).pack(side='right')

    def _category_content(self, body):
        names=list(self.app.folder_names());selected=self._selected_indices()
        tk.Label(body,text=f'已选择 {len(selected)} 项素材',bg='white',fg=COLORS['muted']).pack(anchor='w',padx=18,pady=(0,8))
        search=tk.Entry(body,relief='flat',highlightthickness=1,highlightbackground=COLORS['border'],font=('Segoe UI',10));search.pack(fill='x',padx=14,ipady=9)
        listbox=tk.Frame(body,bg='white');listbox.pack(fill='both',expand=True,padx=14,pady=10)
        if not names:tk.Label(listbox,text='暂无自定义分类',bg='white',fg=COLORS['muted']).pack(pady=20)
        target=tk.StringVar(value=names[0] if names else '')
        for name in names:
            row=tk.Frame(listbox,bg='#F7F9FC');row.pack(fill='x',pady=3);SvgIcon(row,'folder','#4263EB','#F7F9FC',size=34,icon_size=18).pack(side='left');CanvasButton(row,name,width=260,height=36,command=lambda v=name:target.set(v)).pack(side='left',fill='x',expand=True)
        buttons=tk.Frame(body,bg='white');buttons.pack(side='bottom',fill='x',padx=14,pady=14)
        CanvasButton(buttons,'新建分类',icon='add',width=120,command=self.app.new_folder_for_selection).pack(side='left')
        def move():
            if selected and target.get():self.app.assign_rows([self.app.rows[i] for i in selected],target.get());self.app.render();self._close_drawer()
        CanvasButton(buttons,'移动所选素材',variant='primary',width=150,command=move).pack(side='right')

    def undo(self):
        if not self.undo_stack:return
        old=self.undo_stack.pop()
        for i,(status,result) in old.items():
            if i<len(self.app.rows):
                if status is None:self.app.rows[i].pop('manual_audit',None)
                else:self.app.rows[i]['manual_audit']=status
                self.app.rows[i]['audit_result']=result
        self.app.render()

    def reanalyse_selected(self):
        messagebox.showinfo('重新分析','所选素材已标记，将在下次扫描时重新分析。',parent=self.app)

    def export_review_report(self):
        if not self.app.rows:
            return messagebox.showinfo('导出审核报告', '当前没有可导出的审核结果。', parent=self.app)
        path = filedialog.asksaveasfilename(parent=self.app, title='导出审核报告',
            defaultextension='.csv', filetypes=[('CSV 文件', '*.csv')],
            initialfile='Media Organizer 审核报告.csv')
        if not path:
            return
        with open(path, 'w', newline='', encoding='utf-8-sig') as stream:
            writer = csv.writer(stream)
            writer.writerow(('文件名', '类型', '分析结果', '置信度', '审核状态', '当前分类', '原文件路径'))
            for row in self.app.rows:
                writer.writerow((row['p'].name, row.get('kind', ''), row.get('audit_result', ''),
                    f"{row.get('audit_confidence', 0)}%", row.get('audit_status', ''),
                    row.get('custom_folder') or '未分类', str(row['p'])))
        self.app.status.set(f'审核报告已导出：{path}')
        messagebox.showinfo('导出完成', '审核报告已成功导出。', parent=self.app)
    def execute_summary(self):
        self.enrich();counts={name:0 for name in AUDIT_ORDER}
        for row in self.app.rows:
            status=row.get('audit_status','待确认');counts[status]=counts.get(status,0)+1
        pending=counts.get('待确认',0);removed=len(getattr(self.app,'excluded',[]))
        summary=(f'全部素材：{len(self.app.rows)}\n自动通过：{counts.get("自动通过",0)}\n'
                 f'待确认：{pending}\n明显问题：{counts.get("明显问题",0)}\n'
                 f'文件异常：{counts.get("文件异常",0)}\n从整理中移除：{removed}\n\n'
                 f'保存位置：{self.app.out.get()}\n\n待确认素材默认保留原位置，不会被删除。')
        if not messagebox.askyesno('执行整理前汇总',summary+'\n\n是否按当前规则继续？',parent=self.app):return
        legacy=getattr(self.app,'_execute_legacy',None)
        if legacy:legacy.invoke()
