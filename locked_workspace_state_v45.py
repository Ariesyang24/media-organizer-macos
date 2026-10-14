import tkinter as tk

from v3_ui_components import COLORS, CanvasButton, RoundedCard, ToggleSwitch
from recognition_page_state_v40 import WAITING, SCANNING, PAUSED, COMPLETED, FAILED
from state_card_rows_v44 import StateCardRowsV44
from locked_folder_tree_v45 import LockedFolderTreeV45


class LockedWorkspaceStateV45(StateCardRowsV44):
    def __init__(self, app):
        super().__init__(app)
        old=app.folder_tree_panel;parent=old.master;old.destroy();app.folder_tree_panel=LockedFolderTreeV45(parent,app);app.folder_tree_panel.pack(fill='both',expand=True);app.refresh_sidebar()
        self.workspace_overlay=tk.Frame(app.tree.master,bg='white')
        self.overlay_title=tk.StringVar();self.overlay_help=tk.StringVar()
        tk.Label(self.workspace_overlay,textvariable=self.overlay_title,bg='white',fg='#17213C',font=('Segoe UI Semibold',17)).pack()
        tk.Label(self.workspace_overlay,textvariable=self.overlay_help,bg='white',fg=COLORS['muted'],font=('Segoe UI',10)).pack(pady=(7,0))
        self.drawer=None;self.drawer_tab=tk.StringVar(value='识别设置')
        app.unified_workspace.open_drawer=self.open_drawer
        self.apply(COMPLETED if app.rows else WAITING)

    def _overlay(self,title='',help_text=''):
        self.workspace_overlay.place_forget()
        if title:
            self.overlay_title.set(title);self.overlay_help.set(help_text);self.workspace_overlay.place(relx=.5,rely=.5,anchor='center')

    def apply(self,state,error=''):
        # Scanning progress is reported very frequently.  The generic state
        # controller implements SCANNING/PAUSED by first removing the complete
        # workbench and packing a temporary processing card.  Repeating that
        # sequence for every progress event made the real application spend
        # most of a long scan with an empty lower pane (and caused a visible
        # flash whenever the workbench was restored).  These two states share
        # the canonical workbench, so update their header/actions in place and
        # never unmount the workbench.
        if state in (SCANNING, PAUSED) and hasattr(self, 'workspace_overlay'):
            same_state = self.value.get() == state
            self.value.set(state)
            self.error = str(error or '')
            app = self.app
            w = self.waiting

            w.empty.pack_forget()
            self.processing.pack_forget()
            self.error_card.pack_forget()
            if not w.content.winfo_manager():
                w.content.pack(fill='both', expand=True)

            # Progress callbacks may arrive many times per second.  Once the
            # state is established, do not repack buttons or rebuild the
            # folder/audit workspace.  Only the lightweight empty overlay may
            # need to change when the first analysed row becomes available.
            if same_state:
                if app.rows:
                    self._overlay()
                else:
                    title = '扫描已暂停' if state == PAUSED else '正在生成分析结果'
                    help_text = ('当前进度和已完成的分析结果已保留' if state == PAUSED
                                 else '已完成分析的素材会逐步显示在这里')
                    self._overlay(title, help_text)
                    self.workspace_overlay.lift()
                return

            self.show(self.phase_row, fill='x', pady=(5, 4))
            self.show(self.progress_bar, fill='x')
            app.rescan_button.pack_forget()
            app.progress_card_v3.configure(height=190)
            app.v3_phase.set('AI识别与分类')
            if state == SCANNING:
                app.v3_state.set('正在扫描素材')
                app.state_badge.configure(text='AI识别中', bg=COLORS['soft_blue'], fg=COLORS['blue'])
            else:
                app.v3_state.set('扫描已暂停')
                app.state_badge.configure(text='已暂停', bg='#FFF7E8', fg='#9A681B')

            self._show_state_actions(state)
            if app.rows:
                self._overlay()
            else:
                title = '扫描已暂停' if state == PAUSED else '正在生成分析结果'
                help_text = ('当前进度和已完成的分析结果已保留' if state == PAUSED
                             else '已完成分析的素材会逐步显示在这里')
                self._overlay(title, help_text)
                self.workspace_overlay.lift()
            return

        super().apply(state,error)
        if not hasattr(self,'workspace_overlay'):return
        app=self.app;w=self.waiting
        w.empty.pack_forget();self.processing.pack_forget();self.error_card.pack_forget()
        if not w.content.winfo_manager():w.content.pack(fill='both',expand=True)
        self._overlay()
        app.rescan_button.pack_forget()
        if state==WAITING:
            self._overlay('尚未扫描素材','完成扫描后，照片、视频和分析结果会显示在这里')
        elif state==SCANNING:
            if not app.rows:self._overlay('正在生成分析结果','已完成分析的素材会逐步显示在这里')
        elif state==PAUSED:
            if not app.rows:self._overlay('扫描已暂停','当前进度和已完成的分析结果已保留')
        elif state==COMPLETED:
            self.status_action_row.pack_forget();app.progress_card_v3.configure(height=132);app.v3_phase.set('视频镜头与关键帧分析')
            self.show(app.rescan_button,side='right',padx=(0,8),pady=6,before=app.return_selection_button);app.rescan_button.configure(text='重新扫描',icon='rescan',state='normal')
        elif state==FAILED and not app.rows:
            self._overlay('扫描失败',str(error or '扫描任务执行失败'))
        app.unified_workspace.refresh()

    def adapt(self,event=None):
        super().adapt(event)
        if self.value.get()==COMPLETED and hasattr(self,'status_action_row'):
            self.status_action_row.pack_forget()

    def close_drawer(self):
        if self.drawer is not None:
            try:self.drawer.destroy()
            except tk.TclError:pass
        self.drawer=None

    def open_drawer(self,kind='识别设置'):
        self.close_drawer();app=self.app;d=tk.Toplevel(app);self.drawer=d;d.overrideredirect(True);d.transient(app);d.configure(bg=COLORS['border'])
        width=390 if app.winfo_width()>=1500 else 360;height=max(620,app.winfo_height()-38);x=app.winfo_rootx()+app.winfo_width()-width-8;y=app.winfo_rooty()+30;d.geometry(f'{width}x{height}+{x}+{y}')
        shell=tk.Frame(d,bg='white');shell.pack(fill='both',expand=True,padx=1,pady=1)
        tabs=tk.Frame(shell,bg='white');tabs.pack(fill='x',padx=14,pady=(12,6))
        for name in ('识别设置','批量操作','素材详情'):CanvasButton(tabs,name,width=94,height=34,variant='nav-active' if name==kind else 'secondary',command=lambda v=name:self.open_drawer(v)).pack(side='left',padx=(0,4))
        CanvasButton(tabs,'',icon='close',width=34,height=34,command=self.close_drawer).pack(side='right')
        if kind=='批量操作':
            app.unified_workspace._batch_content(shell)
            d.bind('<Escape>',lambda _e:self.close_drawer());d.lift();return
        if kind=='素材详情':
            selected=app.unified_workspace._selected_indices()
            tk.Label(shell,text='素材详情',bg='white',fg='#17213C',font=('Segoe UI Semibold',16)).pack(anchor='w',padx=18,pady=(18,8))
            if not selected:
                tk.Label(shell,text='请先在表格中选择一个素材',bg='white',fg=COLORS['muted']).pack(pady=40)
            else:
                row=app.rows[selected[0]]
                card=RoundedCard(shell,padding=14);card.pack(fill='x',padx=14,pady=8)
                details=(('文件名',row['p'].name),('类型',row.get('kind','')),('分析结果',row.get('audit_result','未分析')),('置信度',f"{row.get('audit_confidence',0)}%"),('审核状态',row.get('audit_status','待确认')),('当前分类',row.get('custom_folder') or '未分类'),('原文件路径',str(row['p'])))
                for label,value in details:
                    line=tk.Frame(card.body,bg='white');line.pack(fill='x',pady=5)
                    tk.Label(line,text=label,bg='white',fg=COLORS['muted'],width=9,anchor='w').pack(side='left')
                    tk.Label(line,text=value,bg='white',fg=COLORS['text'],anchor='w',wraplength=235,justify='left').pack(side='left',fill='x',expand=True)
                actions=tk.Frame(shell,bg='white');actions.pack(fill='x',padx=14,pady=8)
                CanvasButton(actions,'打开原文件',width=142,height=40,command=app.open_original).pack(side='left')
                CanvasButton(actions,'打开视频关键帧',width=168,height=40,command=app.open_keyframes).pack(side='right')
            d.bind('<Escape>',lambda _e:self.close_drawer());d.lift();return
        if kind!='识别设置':
            tk.Label(shell,text=kind,bg='white',fg='#17213C',font=('Segoe UI Semibold',16)).pack(pady=30);d.lift();return
        footer=tk.Frame(shell,bg='white',highlightthickness=1,highlightbackground=COLORS['border']);footer.pack(side='bottom',fill='x')
        CanvasButton(footer,'取消',width=132,height=40,command=self.close_drawer).pack(side='left',padx=12,pady=10);CanvasButton(footer,'保存设置',variant='primary',width=142,height=40,command=self.close_drawer).pack(side='right',padx=12,pady=10)
        canvas=tk.Canvas(shell,bg='white',highlightthickness=0);canvas.pack(fill='both',expand=True);content=tk.Frame(canvas,bg='white');window=canvas.create_window(0,0,anchor='nw',window=content);content.bind('<Configure>',lambda _e:canvas.configure(scrollregion=canvas.bbox('all')));canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width));canvas.bind('<MouseWheel>',lambda e:canvas.yview_scroll(-1 if e.delta>0 else 1,'units'))
        tk.Label(content,text='识别设置',bg='white',fg='#17213C',font=('Segoe UI Semibold',16)).pack(anchor='w',padx=16,pady=(8,0));tk.Label(content,text='设置识别、视频分析与文件安全',bg='white',fg=COLORS['muted']).pack(anchor='w',padx=16,pady=(2,8))
        white=tk.BooleanVar(value=True);subject=tk.BooleanVar(value=True);confidence=tk.BooleanVar(value=True)
        groups=[('常用识别',[('画质、重复、连拍识别',app.smart),('白底商品图保护',white),('主体优先判断',subject)]),('分类识别',[('场景识别并分类',app.scene_on),('模特识别并分类',app.faces_on)]),('视频分析',[('视频镜头、关键帧、画质分析',app.video_on)]),('文件安全',[('复制并保留原文件',app.copy_mode)])]
        for title,options in groups:
            card=RoundedCard(content,padding=10);card.pack(fill='x',padx=12,pady=4);tk.Label(card.body,text=title,bg='white',fg='#17213C',font=('Segoe UI Semibold',10)).pack(anchor='w')
            for text,var in options:
                row=tk.Frame(card.body,bg='white',height=40);row.pack(fill='x');row.pack_propagate(False);tk.Label(row,text=text,bg='white',fg=COLORS['text']).pack(side='left');ToggleSwitch(row,var).pack(side='right',pady=7)
            if title=='常用识别':tk.Label(card.body,text='识别敏感度：  宽松    标准    严格',bg='white',fg=COLORS['blue'],anchor='w').pack(fill='x',pady=4)
            if title=='分类识别':CanvasButton(card.body,'模特分类管理',width=286,height=36,command=getattr(app,'open_people_manager',lambda:None)).pack(fill='x',pady=2)
        card=RoundedCard(content,padding=10);card.pack(fill='x',padx=12,pady=4);tk.Label(card.body,text='界面与导出',bg='white',fg='#17213C',font=('Segoe UI Semibold',10)).pack(anchor='w')
        CanvasButton(card.body,'导出审核报告',width=286,height=36,command=app.unified_workspace.export_review_report).pack(fill='x',pady=2);CanvasButton(card.body,'表格列设置',width=286,height=36,command=app._show_column_settings).pack(fill='x',pady=2)
        row=tk.Frame(card.body,bg='white',height=40);row.pack(fill='x');row.pack_propagate(False);tk.Label(row,text='显示分析置信度',bg='white',fg=COLORS['text']).pack(side='left');ToggleSwitch(row,confidence).pack(side='right',pady=7);CanvasButton(card.body,'恢复默认设置',width=286,height=36,command=lambda:None).pack(fill='x',pady=2)
        d.bind('<Escape>',lambda _e:self.close_drawer());d.lift()
