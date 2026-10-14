import tkinter as tk
from tkinter import messagebox

from v3_ui_components import COLORS, CanvasButton


WAITING='WAITING';SCANNING='SCANNING';PAUSED='PAUSED';COMPLETED='COMPLETED';FAILED='FAILED'


class RecognitionPageStateV39:
    """Single source of truth for recognition-page visibility only."""
    def __init__(self,app):
        self.app=app;self.state=None;self.error=''
        waiting=app.waiting_v38
        self.waiting=waiting
        body=app.progress_card_v3.body
        top=body.pack_slaves()[0]
        textcol=top.pack_slaves()[1]
        self.titleline,self.phase_row,self.progress_bar,self.task_label=textcol.pack_slaves()
        self.detail_button=CanvasButton(top,'查看详情',width=96,height=38,command=self.show_error)
        self.apply(COMPLETED if app.rows else WAITING)

    @staticmethod
    def _hide(widget):
        if widget is not None:widget.pack_forget()
    @staticmethod
    def _show(widget,**options):
        if not widget.winfo_manager():widget.pack(**options)

    def show_error(self):
        messagebox.showerror('扫描失败',self.error or '未知错误',parent=self.app)

    def apply(self,state,error=''):
        self.state=state;self.error=str(error or '')
        a=self.app;w=self.waiting
        # Clear every mutually exclusive action first.
        for widget in (a.pause_button,a.stop_scan_button,w.scan_button,w.scan_hint,
                       a.rescan_button,w.settings_button,self.detail_button):self._hide(widget)
        execute=getattr(getattr(a,'unified_workspace',None),'execute_btn',None)
        self._hide(execute)
        if state==WAITING:
            a.v3_state.set('准备就绪');a.state_badge.configure(text='等待扫描',bg=COLORS['soft_blue'],fg=COLORS['blue'])
            a.v3_phase.set('');a.v3_progress_text.set('');a.v3_percent_text.set('');a.v3_eta.set('')
            a.v3_task.set('添加素材并确认识别设置后开始扫描')
            self._hide(self.phase_row);self._hide(self.progress_bar)
            w.content.pack_forget();self._show(w.empty,fill='both',expand=True)
            self._show(w.settings_button,side='right',padx=(0,8),pady=6,before=a.return_selection_button)
            self._show(w.scan_button,side='right',padx=(12,0));self._show(w.scan_hint,side='right')
            enabled=bool(a.sources);w.scan_button.configure(state='normal' if enabled else 'disabled');w.scan_hint.configure(text='' if enabled else '请先添加素材')
        elif state in (SCANNING,PAUSED):
            w.empty.pack_forget();self._show(w.content,fill='both',expand=True)
            self._show(self.phase_row,fill='x',pady=(5,4));self._show(self.progress_bar,fill='x')
            self._show(a.stop_scan_button,side='right',padx=(8,0))
            self._show(a.pause_button,side='right',padx=(12,0))
            if state==SCANNING:
                a.v3_state.set('正在扫描素材');a.state_badge.configure(text='AI识别中',bg=COLORS['soft_blue'],fg=COLORS['blue'])
                a.pause_button.configure(text='暂停扫描',icon='pause',state='normal')
            else:
                a.v3_state.set('扫描已暂停');a.state_badge.configure(text='已暂停',bg='#FFF7E8',fg='#9A681B')
                a.pause_button.configure(text='继续扫描',icon='play',state='normal')
            a.stop_scan_button.configure(state='normal')
        elif state==COMPLETED:
            w.empty.pack_forget();self._show(w.content,fill='both',expand=True)
            self._show(self.phase_row,fill='x',pady=(5,4));self._show(self.progress_bar,fill='x')
            a.v3_state.set('扫描完成');a.state_badge.configure(text='已完成',bg='#E9F5EF',fg=COLORS['success'])
            a.v3_percent_text.set('100%');a.v3_eta.set('')
            self._show(a.rescan_button,side='right',padx=(0,8),pady=6,before=a.return_selection_button)
            a.rescan_button.configure(text='重新扫描',icon='rescan',state='normal')
            valid=any((r.get('analysis') or {}).get('valid',True) for r in a.rows)
            if execute is not None:
                self._show(execute,side='right')
                execute.configure(state='normal' if valid else 'disabled')
        else:
            w.empty.pack_forget();w.content.pack_forget()
            self._hide(self.phase_row);self._hide(self.progress_bar)
            a.v3_state.set('扫描失败');a.state_badge.configure(text='失败',bg='#FFF1F0',fg=COLORS['warning'])
            a.v3_task.set(self.error or '扫描任务执行失败');a.v3_eta.set('')
            self._show(self.detail_button,side='right',padx=(8,0))
            self._show(a.rescan_button,side='right',padx=(0,8),pady=6,before=a.return_selection_button)
            a.rescan_button.configure(text='重新扫描',icon='rescan',state='normal')
