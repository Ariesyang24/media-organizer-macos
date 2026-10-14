import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scene-runtime'))
builtins.__file__=str(ROOT/'launch_scene_folder_final.pyw')
launcher=ROOT/'launch_media_organizer_safe_drag_v33.pyw'
source=launcher.read_text(encoding='utf-8').rsplit('SafeDragV33MediaOrganizerApp().mainloop()',1)[0]
scope={'__file__':str(launcher)}
exec(compile(source,str(launcher),'exec'),scope)
SafeDragV33MediaOrganizerApp=scope['SafeDragV33MediaOrganizerApp']

class SafeDragV34MediaOrganizerApp(SafeDragV33MediaOrganizerApp):
    def __init__(self):
        super().__init__();self._dashboard_built=False;self._configure_structural_styles();self._build_media_dashboard();self._apply_dashboard_styles();self.minsize(1180,760)
    def _configure_structural_styles(self):
        c=self.COLORS;s=ttk.Style(self)
        s.configure('Dashboard.TFrame',background=c['background'])
        s.configure('Panel.TFrame',background=c['surface'],borderwidth=1,relief='solid',bordercolor=c['border'])
        s.configure('Panel.TLabel',background=c['surface'],foreground=c['text'])
        s.configure('DashboardTitle.TLabel',background=c['surface'],foreground=c['text'],font=('Segoe UI Semibold',17))
        s.configure('DashboardSubtitle.TLabel',background=c['surface'],foreground=c['muted'],font=('Segoe UI',9))
        s.configure('RailTitle.TLabel',background=c['surface'],foreground=c['text'],font=('Segoe UI Semibold',12))
        s.configure('RailMuted.TLabel',background=c['surface'],foreground=c['muted'],font=('Segoe UI',9))
        s.configure('Treeview',rowheight=56)
    def _contains_text(self,root,text):
        for w in (root,*tuple(self._descendants(root))):
            try:
                if str(w.cget('text'))==text:return True
            except (tk.TclError,AttributeError):pass
        return False
    def _owner_with_text(self,children,text):
        return next((w for w in children if self._contains_text(w,text)),None)
    def _direct_owner(self,widget):
        current=widget
        while current is not None and current.master is not self.preview:current=current.master
        return current
    def _move(self,widget,parent,**options):
        if widget is None:return
        try:widget.pack_forget()
        except tk.TclError:pass
        try:widget.grid_forget()
        except tk.TclError:pass
        widget.pack(in_=parent,**options)
    def _panel_heading(self,parent,title,subtitle=''):
        bar=ttk.Frame(parent,style='Panel.TFrame');bar.pack(fill='x',padx=16,pady=(15,8))
        ttk.Label(bar,text=title,style='DashboardTitle.TLabel').pack(anchor='w')
        if subtitle:ttk.Label(bar,text=subtitle,style='DashboardSubtitle.TLabel').pack(anchor='w',pady=(2,0))
    def _build_media_dashboard(self):
        if self._dashboard_built:return
        self._dashboard_built=True
        children=list(self.preview.winfo_children());visible=[w for w in children if w.winfo_manager()]
        stats=next((w for w in children if w.winfo_class()=='TLabelframe' and str(w.cget('text'))=='素材文件夹'),None)
        filters=next((w for w in children if w.winfo_class()=='TLabelframe' and str(w.cget('text'))=='识别结果审核'),None)
        batch=next((w for w in children if w.winfo_class()=='TLabelframe' and str(w.cget('text'))=='批量调整'),None)
        sidebar=self._owner_with_text(children,'文件夹列表');collapse=self._owner_with_text(children,'◀')
        actions=self._owner_with_text(children,'执行整理');recognition=self._owner_with_text(children,'画质/重复/连拍识别');video=self._owner_with_text(children,'视频镜头/关键帧/画质分析');scene=self._owner_with_text(children,'场景识别并分类');more=self._owner_with_text(children,'更多设置 ▸');output=self._owner_with_text(children,'整理保存位置：');progress=self._direct_owner(self.progress)
        hscroll=next((w for w in children if w.winfo_class()=='TScrollbar'),None)
        selected={x for x in (stats,filters,batch,sidebar,collapse,actions,recognition,video,scene,more,output,progress,hscroll,self.tree) if x is not None}
        for w in visible:
            try:w.pack_forget()
            except tk.TclError:pass
        shell=ttk.Frame(self.preview,style='Dashboard.TFrame');shell.pack(fill='both',expand=True,padx=14,pady=12)
        shell.grid_columnconfigure(0,minsize=255,weight=0);shell.grid_columnconfigure(1,minsize=560,weight=1);shell.grid_columnconfigure(2,minsize=300,weight=0);shell.grid_rowconfigure(0,weight=1)
        left=ttk.Frame(shell,style='Panel.TFrame',padding=(0,0));center=ttk.Frame(shell,style='Panel.TFrame',padding=(0,0));right=ttk.Frame(shell,style='Panel.TFrame',padding=(0,0))
        left.grid(row=0,column=0,sticky='nsew',padx=(0,10));center.grid(row=0,column=1,sticky='nsew',padx=(0,10));right.grid(row=0,column=2,sticky='nsew')
        self._panel_heading(left,'素材库','按分类和文件夹快速定位')
        if stats:
            stats.configure(text='快速分类');self._move(stats,left,fill='x',padx=12,pady=(0,10))
            buttons=[w for w in stats.winfo_children() if w.winfo_class()=='TButton']
            for b in buttons:
                b.pack_forget();b.pack(fill='x',padx=7,pady=4)
        if sidebar:self._move(sidebar,left,fill='both',expand=True,padx=12,pady=(0,10))
        if collapse:self._move(collapse,left,fill='x',padx=12,pady=(0,12))
        self._panel_heading(center,'素材审核','查看、筛选并调整本次整理结果')
        if filters:self._move(filters,center,fill='x',padx=14,pady=(0,8))
        if batch:self._move(batch,center,fill='x',padx=14,pady=(0,8))
        self._move(self.tree,center,fill='both',expand=True,padx=14,pady=(0,4))
        if hscroll:self._move(hscroll,center,fill='x',padx=14,pady=(0,12))
        self._panel_heading(right,'识别与整理','控制识别方式并完成输出')
        if progress:self._move(progress,right,fill='x',padx=14,pady=(0,10))
        if recognition:self._move(recognition,right,fill='x',padx=14,pady=4)
        if scene:self._move(scene,right,fill='x',padx=14,pady=4)
        if video:self._move(video,right,fill='x',padx=14,pady=4)
        if more:self._move(more,right,fill='x',padx=14,pady=(8,4))
        ttk.Separator(right).pack(fill='x',padx=14,pady=10)
        if output:self._move(output,right,fill='x',padx=14,pady=4)
        if actions:
            self._move(actions,right,fill='x',padx=14,pady=(10,14))
            for child in actions.winfo_children():
                try:child.pack_forget();child.pack(fill='x',pady=3)
                except tk.TclError:pass
        self.dashboard_shell=shell;self.dashboard_columns=(left,center,right);self._apply_dashboard_styles()
    def render(self):
        super().render();self.after_idle(self._apply_dashboard_styles)

SafeDragV34MediaOrganizerApp().mainloop()
