import tkinter as tk
from tkinter import messagebox

from v3_ui_components import COLORS,CanvasButton,RoundedCard
from svg_icon_system import SvgIcon

WAITING='WAITING';SCANNING='SCANNING';PAUSED='PAUSED';COMPLETED='COMPLETED';FAILED='FAILED'


class RecognitionPageStateV40:
    def __init__(self,app):
        self.app=app;self.value=tk.StringVar(value=WAITING);self.error='';self.waiting=app.waiting_v38
        root=app.v3_recognition_root;body=app.progress_card_v3.body;top=body.pack_slaves()[0];textcol=top.pack_slaves()[1]
        self.titleline,self.phase_row,self.progress_bar,self.task_label=textcol.pack_slaves()
        self.detail=CanvasButton(top,'查看详情',width=96,height=38,command=self.show_error)
        self.processing=RoundedCard(root,height=300,padding=24)
        center=tk.Frame(self.processing.body,bg='white');center.place(relx=.5,rely=.5,anchor='center')
        SvgIcon(center,'scan',COLORS['blue'],'#EEF2FF',size=64,icon_size=30).pack(pady=(0,14))
        tk.Label(center,text='正在生成分析结果',bg='white',fg='#17213C',font=('Segoe UI Semibold',16)).pack()
        tk.Label(center,text='扫描完成后可开始审核',bg='white',fg=COLORS['muted'],font=('Segoe UI',10)).pack(pady=(6,0))
        app.bind('<Configure>',self.adapt,add='+')
        self.apply(COMPLETED if app.rows else WAITING)

    def hide(self,w):
        if w is not None:w.pack_forget()
    def show(self,w,**kw):
        if not w.winfo_manager():w.pack(**kw)

    def clear_actions(self):
        a=self.app;w=self.waiting
        for item in (a.pause_button,a.stop_scan_button,w.scan_button,w.scan_hint,a.rescan_button,w.settings_button,self.detail):self.hide(item)
        execute=getattr(getattr(a,'unified_workspace',None),'execute_btn',None);self.hide(execute)

    def apply(self,state,error=''):
        self.value.set(state);self.error=str(error or '');a=self.app;w=self.waiting;self.clear_actions()
        w.empty.pack_forget();self.processing.pack_forget();w.content.pack_forget()
        if state==WAITING:
            a.v3_state.set('准备就绪');a.state_badge.configure(text='等待扫描',bg=COLORS['soft_blue'],fg=COLORS['blue'])
            a.v3_phase.set('');a.v3_progress_text.set('');a.v3_percent_text.set('');a.v3_eta.set('');a.v3_task.set('添加素材并确认识别设置后开始扫描')
            self.hide(self.phase_row);self.hide(self.progress_bar);self.show(w.empty,fill='both',expand=True)
            self.show(w.settings_button,side='right',padx=(0,8),pady=6,before=a.return_selection_button)
            self.show(w.scan_button,side='right',padx=(12,0));self.show(w.scan_hint,side='right')
            enabled=bool(a.sources);w.scan_button.configure(state='normal' if enabled else 'disabled');w.scan_hint.configure(text='' if enabled else '请先添加素材')
        elif state in (SCANNING,PAUSED):
            self.show(self.phase_row,fill='x',pady=(5,4));self.show(self.progress_bar,fill='x');self.show(self.processing,fill='both',expand=True)
            self.show(a.stop_scan_button,side='right',padx=(8,0));self.show(a.pause_button,side='right',padx=(12,0));a.stop_scan_button.configure(state='normal')
            if state==SCANNING:
                a.v3_state.set('正在扫描素材');a.state_badge.configure(text='AI识别中',bg=COLORS['soft_blue'],fg=COLORS['blue']);a.pause_button.configure(text='暂停扫描',icon='pause',state='normal')
            else:
                a.v3_state.set('扫描已暂停');a.state_badge.configure(text='已暂停',bg='#FFF7E8',fg='#9A681B');a.pause_button.configure(text='继续扫描',icon='play',state='normal')
        elif state==COMPLETED:
            self.show(self.phase_row,fill='x',pady=(5,4));self.show(self.progress_bar,fill='x');self.show(w.content,fill='both',expand=True)
            a.v3_state.set('扫描完成');a.state_badge.configure(text='已完成',bg='#E9F5EF',fg=COLORS['success']);a.v3_eta.set('')
            total=len(a.rows);a.v3_progress_text.set(f'{total} / {total}');a.v3_percent_text.set('100%');a.v3_progress_value.set(100)
            pending=sum(r.get('audit_status')=='待确认' for r in a.rows);problems=sum(r.get('audit_status')=='明显问题' for r in a.rows);failed=sum(r.get('audit_status')=='文件异常' for r in a.rows)
            elapsed=max(0.0,__import__('time').monotonic()-(a.scan_started_at or __import__('time').monotonic()))
            a.v3_task.set(f'扫描耗时 {elapsed:.1f} 秒 · 待确认 {pending} 项 · 明显问题 {problems} 项 · 文件异常 {failed} 项')
            self.show(a.rescan_button,side='right',padx=(0,8),pady=6,before=a.return_selection_button);a.rescan_button.configure(text='重新扫描',icon='rescan',state='normal')
            execute=getattr(getattr(a,'unified_workspace',None),'execute_btn',None);valid=any((r.get('analysis') or {}).get('valid',True) for r in a.rows)
            if execute is not None:self.show(execute,side='right');execute.configure(state='normal' if valid else 'disabled')
        else:
            self.hide(self.phase_row);self.hide(self.progress_bar);a.v3_state.set('扫描失败');a.state_badge.configure(text='失败',bg='#FFF1F0',fg=COLORS['warning']);a.v3_task.set(self.error or '扫描任务执行失败');a.v3_eta.set('')
            self.show(self.detail,side='right',padx=(8,0));self.show(a.rescan_button,side='right',padx=(0,8),pady=6,before=a.return_selection_button);a.rescan_button.configure(text='重新扫描',icon='rescan',state='normal')
        self.adapt()

    def show_error(self):messagebox.showerror('扫描失败',self.error or '未知错误',parent=self.app)

    def adapt(self,_event=None):
        a=self.app;width=max(1,a.winfo_width());a.sidebar_v3.configure(width=220 if a.sidebar_expanded else 72)
        # At narrower widths, retain primary filters/actions and move visual priority to More.
        toolbar=getattr(getattr(a,'unified_workspace',None),'toolbar',None)
        if toolbar is None:return
        line=toolbar.pack_slaves()[0]
        low={'相似项分组','移动到分类','识别设置'}
        for button in line.pack_slaves():
            try:text=button.cget('text')
            except tk.TclError:continue
            if text in low:
                if width<1450:button.pack_forget()
                elif not button.winfo_manager():button.pack(side='left',padx=4,before=getattr(a.unified_workspace,'more_btn',None))
