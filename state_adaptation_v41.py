import tkinter as tk
from v3_ui_components import COLORS,CanvasButton,RoundedCard
from recognition_page_state_v40 import RecognitionPageStateV40,WAITING,SCANNING,PAUSED,COMPLETED,FAILED
from audit_folder_tree_v41 import AuditFolderTreeV41


class StateAdaptationV41(RecognitionPageStateV40):
    def __init__(self,app):
        self.ready=False;self.auto_collapsed=False
        super().__init__(app)
        top=app.pause_button.master
        self.card_rescan=CanvasButton(top,'重新扫描',icon='rescan',width=112,height=38,command=app.start_scan)
        self.card_detail=CanvasButton(top,'查看详情',width=96,height=38,command=self.show_error)
        root=app.v3_recognition_root
        self.error_card=RoundedCard(root,height=260,padding=24)
        self.error_title=tk.StringVar(value='扫描失败');self.error_stage=tk.StringVar(value='失败阶段：扫描与分析');self.error_summary=tk.StringVar(value='')
        c=tk.Frame(self.error_card.body,bg='white');c.place(relx=.5,rely=.45,anchor='center')
        tk.Label(c,textvariable=self.error_title,bg='white',fg=COLORS['warning'],font=('Segoe UI Semibold',18)).pack()
        tk.Label(c,textvariable=self.error_stage,bg='white',fg='#17213C',font=('Segoe UI Semibold',10)).pack(pady=(12,4))
        tk.Label(c,textvariable=self.error_summary,bg='white',fg=COLORS['muted'],font=('Segoe UI',10),wraplength=620).pack()
        self._replace_folder_panel();self.ready=True;self.apply(COMPLETED if app.rows else WAITING)

    def _replace_folder_panel(self):
        app=self.app;old=app.folder_tree_panel;parent=old.master;old.destroy();app.folder_tree_panel=AuditFolderTreeV41(parent,app);app.folder_tree_panel.pack(fill='both',expand=True);app.refresh_sidebar()

    def clear_actions(self):
        super().clear_actions()
        if hasattr(self,'card_rescan'):self.hide(self.card_rescan);self.hide(self.card_detail)

    def apply(self,state,error=''):
        if hasattr(self,'error_card'):self.error_card.pack_forget()
        super().apply(state,error)
        if not getattr(self,'ready',False):return
        a=self.app
        # Completed and failed actions live inside the scan card, never outside the window.
        a.rescan_button.pack_forget()
        if state==COMPLETED:self.show(self.card_rescan,side='right',padx=(8,0))
        elif state==FAILED:
            self.error_summary.set(str(error or '扫描任务执行失败'))
            self.show(self.card_detail,side='right',padx=(8,0));self.show(self.card_rescan,side='right',padx=(8,0));self.show(self.error_card,fill='both',expand=True)
        self.adapt()

    def adapt(self,_event=None):
        if not getattr(self,'ready',False):return super().adapt(_event)
        a=self.app;width=max(1,a.winfo_width())
        # Auto-collapse once on narrow windows, but never fight a manual click.
        # Previously every <Configure> event immediately closed a sidebar that
        # the user had just opened, making the toggle appear broken.
        manual_override = getattr(a, 'sidebar_manual_override', False)
        if width<=1320 and a.sidebar_expanded and not manual_override:
            self.auto_collapsed=True;a._apply_sidebar(False)
        elif width>1320 and self.auto_collapsed and not a.sidebar_expanded and not manual_override:
            self.auto_collapsed=False;a._apply_sidebar(True)
        target_sidebar_width=220 if a.sidebar_expanded else 72
        # Reconfiguring an unchanged width emits another Configure event on
        # Windows/Tk. That feedback loop repeatedly repainted the folder tree
        # and was the remaining source of the visible sidebar flashing.
        if int(a.sidebar_v3.cget('width')) != target_sidebar_width:
            a.sidebar_v3.configure(width=target_sidebar_width)
        content=self.waiting.content
        if content.winfo_exists() and content.pack_slaves():
            left=content.pack_slaves()[0];left.configure(width=240 if width<=1320 else 260 if width<1800 else 300)
        tree=a.tree
        try:
            if not tree.winfo_exists():return
        except tk.TclError:return
        if width<=1320:
            visible=tuple(c for c in ('file','kind','quality','recommend','video') if c in tree['columns'])
        elif width<1600:
            visible=tuple(c for c in ('file','kind','quality','recommend','target','video') if c in tree['columns'])
        else:
            visible=tuple(c for c in ('file','kind','quality','duplicate','recommend','target','video') if c in tree['columns'])
        tree.configure(displaycolumns=visible)
        toolbar=getattr(getattr(a,'unified_workspace',None),'toolbar',None)
        if toolbar is None:return
        line=toolbar.pack_slaves()[0];low={'相似项分组','移动到分类','识别设置'}
        more=a.unified_workspace.more_btn
        for button in list(line.winfo_children()):
            try:text=button.cget('text')
            except tk.TclError:continue
            if text in low:
                if width<1800:button.pack_forget()
                elif not button.winfo_manager():button.pack(side='left',padx=4,before=more)
        more.configure(command=self.show_more)

    def show_more(self):
        a=self.app;selected=bool(a.tree.selection());a._popup_actions([
            ('相似项分组',a.unified_workspace.select_similar_group,True),
            ('移动到分类',lambda:a.unified_workspace.open_drawer('分类管理'),True),
            ('识别设置',lambda:a.waiting_v38.open_settings(),True),
            ('打开原文件',a.open_original,selected),('打开视频关键帧',a.open_keyframes,selected),
            ('从整理中移除',a.remove_selected_from_plan,selected and not a.scan_busy)],more if (more:=a.unified_workspace.more_btn) else None)
