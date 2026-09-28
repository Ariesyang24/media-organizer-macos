from pathlib import Path

namespace={}
source=Path(__file__).with_name('review_workflow_fixed.pyw').read_text(encoding='utf-8').rsplit('ReviewFixedApp().mainloop()',1)[0]
exec(compile(source,'review_workflow_fixed.pyw','exec'),namespace)
ReviewFixedApp=namespace['ReviewFixedApp']

class CleanUIApp(ReviewFixedApp):
    def __init__(self):
        super().__init__();self.title('Media Organizer · Windows 智能素材整理')
        if getattr(self,'step_labels',None):self.step_labels[0].master.destroy()
        self._rebuild_setup();self.book.tab(self.setup,text='添加素材');self.book.tab(self.preview,text='识别与整理')
        self.status.set('拖入素材文件夹，确认排除目录和输出位置，然后扫描')
    def _rebuild_setup(self):
        for child in self.setup.winfo_children():child.destroy()
        shell=ttk.Frame(self.setup,padding=18);shell.pack(fill='both',expand=True)
        title=ttk.Frame(shell);title.pack(fill='x',pady=(0,12));ttk.Label(title,text='准备素材',font=('Segoe UI',16,'bold')).pack(anchor='w');ttk.Label(title,text='添加一个或多个来源；成片、精修图和输出目录不会参与扫描。').pack(anchor='w',pady=(3,0))
        columns=ttk.Frame(shell);columns.pack(fill='both',expand=True);left=ttk.LabelFrame(columns,text='1  素材来源',padding=12);right=ttk.LabelFrame(columns,text='2  排除与输出',padding=12);left.pack(side='left',fill='both',expand=True,padx=(0,7));right.pack(side='left',fill='both',expand=True,padx=(7,0))
        ttk.Label(left,text='可拖入多个文件夹',foreground='#555').pack(anchor='w');self.src_box=tk.Listbox(left,height=12,selectmode='extended');self.src_box.pack(fill='both',expand=True,pady=8);self.src_box.drop_target_register(namespace['DND_FILES']);self.src_box.dnd_bind('<<Drop>>',self.drop_src)
        buttons=ttk.Frame(left);buttons.pack(fill='x');ttk.Button(buttons,text='＋ 添加文件夹',command=self.add_source).pack(side='left');ttk.Button(buttons,text='移除选中',command=self.remove_source).pack(side='left',padx=6);ttk.Label(buttons,text='把文件夹拖到上方列表也可以',foreground='#666').pack(side='right')
        ttk.Label(right,text='不参与整理的目录',foreground='#555').pack(anchor='w');self.exc_box=tk.Listbox(right,height=6,selectmode='extended');self.exc_box.pack(fill='x',pady=8);self.exc_box.drop_target_register(namespace['DND_FILES']);self.exc_box.dnd_bind('<<Drop>>',self.drop_exc)
        exclude_buttons=ttk.Frame(right);exclude_buttons.pack(fill='x');ttk.Button(exclude_buttons,text='＋ 添加排除目录',command=self.add_exclusion).pack(side='left');ttk.Button(exclude_buttons,text='移除选中',command=self.remove_exclusion).pack(side='left',padx=6)
        ttk.Separator(right).pack(fill='x',pady=14);ttk.Label(right,text='目录命名').pack(anchor='w');langs=ttk.Frame(right);langs.pack(fill='x',pady=5);ttk.Radiobutton(langs,text='中文目录',variable=self.english,value=False,command=self.retarget).pack(side='left');ttk.Radiobutton(langs,text='English folders',variable=self.english,value=True,command=self.retarget).pack(side='left',padx=16)
        ttk.Label(right,text='整理后的保存位置').pack(anchor='w',pady=(12,3));outrow=ttk.Frame(right);outrow.pack(fill='x');ttk.Entry(outrow,textvariable=self.out).pack(side='left',fill='x',expand=True);ttk.Button(outrow,text='浏览…',command=self.output).pack(side='left',padx=(6,0))
        footer=ttk.Frame(shell);footer.pack(fill='x',pady=(14,0));ttk.Label(footer,text='默认只复制并保留原文件；识别结果会在下一页预览。',foreground='#555').pack(side='left');ttk.Button(footer,text='扫描并预览 →',command=self.start_scan).pack(side='right')

CleanUIApp().mainloop()
