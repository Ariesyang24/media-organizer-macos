import tkinter as tk

from v3_ui_components import COLORS, CanvasButton, RoundedCard, ToggleSwitch
from svg_icon_system import SvgIcon


class WaitingStateV38:
    """Only controls the zero-assets, not-scanning presentation."""

    def __init__(self, app):
        self.app = app
        self.drawer = None
        root = app.v3_recognition_root
        packed = root.pack_slaves()
        self.content = packed[-1]
        self.header = packed[0]
        app.rescan_button.pack_forget()
        self.settings_button = CanvasButton(self.header, '识别设置', icon='settings', width=112,
                                            command=self.open_settings)
        self.settings_button.pack(side='right', padx=(0, 8), pady=6, before=app.return_selection_button)

        progress_top = app.pause_button.master
        self.scan_button = CanvasButton(progress_top, '扫描并预览', icon='scan', variant='primary',
                                        width=132, height=40, command=app.start_scan)
        self.scan_button.pack(side='right', padx=(12, 0))
        self.scan_hint = tk.Label(progress_top, text='请先添加素材', bg='white', fg=COLORS['muted'],
                                  font=('Segoe UI', 8))
        self.scan_hint.pack(side='right')

        self.empty = RoundedCard(root, height=360, padding=24)
        center = tk.Frame(self.empty.body, bg='white'); center.place(relx=.5, rely=.5, anchor='center')
        SvgIcon(center, 'folder', COLORS['blue'], '#EEF2FF', size=64, icon_size=30).pack(pady=(0, 14))
        tk.Label(center, text='尚未扫描素材', bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 17)).pack()
        tk.Label(center, text='完成扫描后，照片、视频和分析结果会显示在这里', bg='white',
                 fg=COLORS['muted'], font=('Segoe UI', 10)).pack(pady=(6, 18))
        actions = tk.Frame(center, bg='white'); actions.pack()
        CanvasButton(actions, '添加素材', icon='add', width=122, height=40,
                     command=lambda: app._select_page(0)).pack(side='left', padx=5)
        CanvasButton(actions, '识别设置', icon='settings', width=122, height=40,
                     command=self.open_settings).pack(side='left', padx=5)
        self.refresh()

    def refresh(self):
        waiting = not self.app.rows and not self.app.scan_busy
        if not waiting:
            self.empty.pack_forget()
            if not self.content.winfo_manager(): self.content.pack(fill='both', expand=True)
            return
        self.app.v3_state.set('准备就绪')
        self.app.v3_phase.set('等待扫描')
        self.app.v3_progress_text.set('')
        self.app.v3_percent_text.set('')
        self.app.v3_task.set('添加素材并确认识别设置后开始扫描')
        self.app.v3_eta.set('')
        self.app.state_badge.configure(text='等待扫描', bg=COLORS['soft_blue'], fg=COLORS['blue'])
        self.app.pause_button.pack_forget(); self.app.stop_scan_button.pack_forget()
        self.content.pack_forget()
        if not self.empty.winfo_manager(): self.empty.pack(fill='both', expand=True)
        enabled = bool(self.app.sources)
        self.scan_button.configure(state='normal' if enabled else 'disabled')
        self.scan_hint.configure(text='' if enabled else '请先添加素材')

    def close(self):
        if self.drawer is not None:
            try: self.drawer.destroy()
            except tk.TclError: pass
        self.drawer = None

    def open_settings(self):
        if self.drawer is not None and self.drawer.winfo_exists(): self.close(); return
        app=self.app; d=tk.Toplevel(app); self.drawer=d
        d.overrideredirect(True);d.transient(app);d.configure(bg=COLORS['border'])
        width=360;height=max(620,app.winfo_height()-38);x=app.winfo_rootx()+app.winfo_width()-width-8;y=app.winfo_rooty()+30
        d.geometry(f'{width}x{height}+{x}+{y}')
        shell=tk.Frame(d,bg='white');shell.pack(fill='both',expand=True,padx=1,pady=1)
        head=tk.Frame(shell,bg='white');head.pack(fill='x',padx=16,pady=(14,8))
        tk.Label(head,text='识别设置',bg='white',fg='#17213C',font=('Segoe UI Semibold',16)).pack(side='left')
        CanvasButton(head,'',icon='close',width=36,height=36,command=self.close).pack(side='right')
        tk.Label(shell,text='设置识别、视频分析与文件安全',bg='white',fg=COLORS['muted']).pack(anchor='w',padx=16,pady=(0,8))
        footer=tk.Frame(shell,bg='white',highlightthickness=1,highlightbackground=COLORS['border']);footer.pack(side='bottom',fill='x')
        CanvasButton(footer,'取消',width=132,height=40,command=self.close).pack(side='left',padx=12,pady=10)
        CanvasButton(footer,'保存设置',variant='primary',width=142,height=40,command=self.close).pack(side='right',padx=12,pady=10)
        canvas=tk.Canvas(shell,bg='white',highlightthickness=0,bd=0);canvas.pack(fill='both',expand=True)
        content=tk.Frame(canvas,bg='white');window=canvas.create_window(0,0,anchor='nw',window=content)
        content.bind('<Configure>',lambda _e:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
        canvas.bind('<MouseWheel>',lambda e:canvas.yview_scroll(-1 if e.delta>0 else 1,'units'))
        white_protect=tk.BooleanVar(value=True);subject_first=tk.BooleanVar(value=True);confidence=tk.BooleanVar(value=True)
        groups=[('常用识别',[('画质、重复、连拍识别',app.smart),('白底商品图保护',white_protect),('主体优先判断',subject_first)]),
                ('分类识别',[('场景识别并分类',app.scene_on),('模特识别并分类',app.faces_on)]),
                ('视频分析',[('视频镜头、关键帧、画质分析',app.video_on)]),
                ('文件安全',[('复制并保留原文件',app.copy_mode)])]
        for title,options in groups:
            section=self._section(content,title)
            for text,var in options:self._option(section,text,var)
            if title=='常用识别':
                row=tk.Frame(section,bg='white',height=44);row.pack(fill='x');row.pack_propagate(False)
                tk.Label(row,text='灵敏度',bg='white',fg=COLORS['text']).pack(side='left')
                tk.Label(row,text='宽松   标准   严格',bg='white',fg=COLORS['blue']).pack(side='right')
            if title=='分类识别':
                CanvasButton(section,'模特分类管理',width=286,height=40,
                             command=getattr(app,'open_people_manager',lambda:None)).pack(fill='x',pady=2)
        interface=self._section(content,'界面与导出')
        CanvasButton(interface,'导出审核报告',width=286,height=40,command=lambda:None).pack(fill='x',pady=2)
        CanvasButton(interface,'表格列设置',width=286,height=40,command=app._show_column_settings).pack(fill='x',pady=2)
        self._option(interface,'显示分析置信度',confidence)
        CanvasButton(interface,'恢复默认设置',width=286,height=40,command=lambda:None).pack(fill='x',pady=2)
        d.bind('<Escape>',lambda _e:self.close());d.lift()

    def _section(self,parent,title):
        card=RoundedCard(parent,padding=10);card.pack(fill='x',padx=12,pady=4)
        tk.Label(card.body,text=title,bg='white',fg='#17213C',font=('Segoe UI Semibold',10)).pack(anchor='w',pady=(0,3))
        return card.body

    def _option(self,parent,text,var):
        row=tk.Frame(parent,bg='white',height=44);row.pack(fill='x');row.pack_propagate(False)
        tk.Label(row,text=text,bg='white',fg=COLORS['text']).pack(side='left')
        ToggleSwitch(row,var).pack(side='right',pady=9)
