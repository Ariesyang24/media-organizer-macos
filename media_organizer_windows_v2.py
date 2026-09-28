from media_organizer_windows import *

class FullApp(App):
    def __init__(self):
        tk.Tk.__init__(self); self.title('Media Organizer · Windows'); self.geometry('1280x820'); self.minsize(1080,720)
        self.sources=[]; self.excludes=[]; self.rows=[]; self.stop=threading.Event(); self.out=tk.StringVar(value=str(Path.home()/'Pictures'/'所有素材')); self.status=tk.StringVar(value='请选择素材范围')
        self.place=tk.StringVar(); self.english=tk.BooleanVar(); self.copy_mode=tk.BooleanVar(value=True); self.rename_on=tk.BooleanVar(); self.rename_base=tk.StringVar(); self.auto_places={}; self.busy=False
        self.build_full()
    def build_full(self):
        head=ttk.Frame(self,padding=12); head.pack(fill='x'); ttk.Label(head,text='Media Organizer',font=('Segoe UI',18,'bold')).pack(side='left'); ttk.Label(head,text='  按日期地点、设备和素材类型安全分类').pack(side='left'); self.action=ttk.Button(head,text='扫描并预览',command=self.start_scan); self.action.pack(side='right')
        steps=ttk.Frame(self,padding=(20,8)); steps.pack(fill='x'); self.step_labels=[]
        for text in ('① 选择范围','② 扫描识别','③ 预览与整理'):
            x=ttk.Label(steps,text=text,anchor='center',padding=8); x.pack(side='left',fill='x',expand=True); self.step_labels.append(x)
        self.book=ttk.Notebook(self); self.book.pack(fill='both',expand=True,padx=14,pady=6); self.setup=ttk.Frame(self.book); self.preview=ttk.Frame(self.book); self.book.add(self.setup,text='选择范围'); self.book.add(self.preview,text='预览与整理')
        left=ttk.LabelFrame(self.setup,text='素材来源',padding=10); right=ttk.LabelFrame(self.setup,text='排除与输出',padding=10); left.pack(side='left',fill='both',expand=True,padx=(8,4),pady=8); right.pack(side='left',fill='both',expand=True,padx=(4,8),pady=8)
        self.src_box=tk.Listbox(left,height=16); self.src_box.pack(fill='both',expand=True); ttk.Button(left,text='添加素材文件夹…',command=self.add_source).pack(fill='x',pady=5); ttk.Button(left,text='移除选中',command=self.remove_source).pack(fill='x')
        ttk.Label(right,text='成片、精修图等目录不参与整理').pack(anchor='w'); self.exc_box=tk.Listbox(right,height=9); self.exc_box.pack(fill='both',expand=True,pady=5); ttk.Button(right,text='添加排除目录…',command=self.add_exclusion).pack(fill='x'); ttk.Button(right,text='移除选中',command=self.remove_exclusion).pack(fill='x',pady=(4,12))
        ttk.Label(right,text='目录命名语言').pack(anchor='w'); ttk.Radiobutton(right,text='中文',variable=self.english,value=False,command=self.retarget).pack(anchor='w'); ttk.Radiobutton(right,text='English',variable=self.english,value=True,command=self.retarget).pack(anchor='w')
        ttk.Label(right,text='总素材文件夹').pack(anchor='w',pady=(10,0)); ttk.Entry(right,textvariable=self.out).pack(fill='x'); ttk.Button(right,text='更改保存位置…',command=self.output).pack(fill='x',pady=5)
        cards=ttk.Frame(self.preview); cards.pack(fill='x',padx=8,pady=5); self.stats=[]
        for name in ('全部','照片','视频','失败/跳过'):
            v=tk.StringVar(value=f'0\n{name}'); self.stats.append(v); ttk.Label(cards,textvariable=v,anchor='center',padding=10,relief='groove').pack(side='left',fill='x',expand=True,padx=3)
        batch=ttk.LabelFrame(self.preview,text='批次地点修正',padding=8); batch.pack(fill='x',padx=8,pady=4); ttk.Label(batch,text='在下表多选素材后统一修改地点；“恢复自动”撤销手动值。').pack(side='left'); ttk.Entry(batch,textvariable=self.place,width=24).pack(side='left',padx=8); ttk.Button(batch,text='应用地点',command=self.apply_place).pack(side='left'); ttk.Button(batch,text='恢复自动',command=self.restore_place).pack(side='left',padx=4)
        rename=ttk.LabelFrame(self.preview,text='照片文件重命名（可选）',padding=8); rename.pack(fill='x',padx=8,pady=4); ttk.Checkbutton(rename,text='启用',variable=self.rename_on).pack(side='left'); ttk.Label(rename,text='所选照片按拍摄时间编号；同名 RAW+JPG 保持同号：').pack(side='left'); ttk.Entry(rename,textvariable=self.rename_base,width=24).pack(side='left'); ttk.Label(rename,text='_0001').pack(side='left')
        opts=ttk.Frame(self.preview,padding=8); opts.pack(fill='x'); ttk.Checkbutton(opts,text='复制并保留原文件（推荐）',variable=self.copy_mode).pack(side='left'); ttk.Button(opts,text='返回选择',command=lambda:self.book.select(self.setup)).pack(side='right'); ttk.Button(opts,text='重新扫描',command=self.start_scan).pack(side='right',padx=5); ttk.Button(opts,text='执行整理',command=self.start_run).pack(side='right')
        cols=('file','date','place','source','device','kind','target'); self.tree=ttk.Treeview(self.preview,columns=cols,show='headings',selectmode='extended')
        for c,n,w in zip(cols,['文件','日期','地点','来源','设备（可改）','类型','目标路径'],[150,85,110,65,160,55,430]): self.tree.heading(c,text=n); self.tree.column(c,width=w,anchor='w')
        self.tree.pack(fill='both',expand=True,padx=8,pady=4); self.tree.bind('<Double-1>',self.edit_device)
        self.progress=ttk.Progressbar(self); self.progress.pack(fill='x',padx=14); ttk.Label(self,textvariable=self.status,padding=10).pack(fill='x')
    def add_source(self):
        if (x:=filedialog.askdirectory(title='选择素材来源')) and Path(x) not in self.sources: self.sources.append(Path(x)); self.src_box.insert('end',x)
    def add_exclusion(self):
        if (x:=filedialog.askdirectory(title='选择排除目录')) and Path(x) not in self.excludes: self.excludes.append(Path(x)); self.exc_box.insert('end',x)
    def remove_source(self):
        for i in reversed(self.src_box.curselection()): del self.sources[i]; self.src_box.delete(i)
    def remove_exclusion(self):
        for i in reversed(self.exc_box.curselection()): del self.excludes[i]; self.exc_box.delete(i)
    def start_scan(self):
        if not self.sources:return messagebox.showwarning('提示','请先添加素材来源')
        self.stop.clear(); self.status.set('正在扫描识别…'); threading.Thread(target=self.scan,daemon=True).start()
    def retarget(self):
        if not self.rows:return
        known={r['p'].parent:r['dev'] for r in self.rows if r['dev']!='未知设备'}; groups={}
        for r in self.rows:
            r['dev']=known.get(r['p'].parent,r['dev']); place=self.comp(r['place']); day=r['date'].replace('-','.'); key=(day+' '+place,self.comp(r['dev'])); groups.setdefault(key,set()).add(r['p'].parent)
        nums={}
        for key,folders in groups.items():
            if len(folders)>1:
                for i,f in enumerate(sorted(folders),1):nums[key+(f,)]=f'{i:03d}'
        for r in self.rows:
            day=r['date'].replace('-','.'); place=self.comp(r['place']); dev=self.comp(r['dev']); kind=('Photos' if r['kind']=='照片' else 'Videos') if self.english.get() else r['kind']; target=Path(day+' '+place)/f'{dev} {kind}'; num=nums.get((day+' '+place,dev,r['p'].parent))
            if num:target/=num
            r['target']=str(target)
        self.render()
    def comp(self,s):
        if not self.english.get():return safe(s)
        s={'未设置':'Unknown Location','未知设备':'Unknown Device'}.get(s,s); return re.sub(r'[ _-]+',' ',re.sub(r'[^A-Za-z0-9._ -]+','-',s)).strip() or 'Unknown'
    def render(self):
        for r in self.rows:self.auto_places.setdefault(str(r['p']),r['place'])
        self.retarget_once=False; self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(self.rows):self.tree.insert('', 'end',iid=str(i),values=(r['p'].name,r['date'],r['place'],'手动' if r.get('manual') else '自动',r['dev'],r['kind'],r['target']))
        photos=sum(r['kind']=='照片' for r in self.rows); self.stats[0].set(f'{len(self.rows)}\n全部'); self.stats[1].set(f'{photos}\n照片'); self.stats[2].set(f'{len(self.rows)-photos}\n视频'); self.stats[3].set('0\n失败/跳过'); self.book.select(self.preview); self.action.configure(text='执行整理',command=self.start_run)
    def apply_place(self):
        v=self.place.get().strip()
        if not v:return
        for x in self.tree.selection():self.rows[int(x)]['place']=v; self.rows[int(x)]['manual']=True
        self.retarget()
    def restore_place(self):
        for x in self.tree.selection():
            r=self.rows[int(x)];r['place']=self.auto_places.get(str(r['p']),'未设置');r['manual']=False
        self.retarget()
    def edit_device(self,event):
        item=self.tree.identify_row(event.y); col=self.tree.identify_column(event.x)
        if item and col=='#5':
            value=tk.simpledialog.askstring('修改设备','设备名称：',initialvalue=self.rows[int(item)]['dev'],parent=self)
            if value:self.rows[int(item)]['dev']=value;self.retarget()
    def start_run(self):
        if not self.rows:return messagebox.showwarning('提示','请先扫描')
        out=Path(self.out.get()); need=sum(r['p'].stat().st_size for r in self.rows); out.mkdir(parents=True,exist_ok=True)
        if self.copy_mode.get() and shutil.disk_usage(out).free<need:return messagebox.showerror('空间不足','目标磁盘空间不足')
        if messagebox.askyesno('确认整理',f'目标：{out}\n方式：{"复制并保留原文件" if self.copy_mode.get() else "移动原文件（有风险）"}\n数量：{len(self.rows)}\n大小：{need/1048576:.1f} MB'):threading.Thread(target=self.full_run,args=(out,),daemon=True).start()
    def full_run(self,out):
        originals=[r['p'].name for r in self.rows]; stems={};
        if self.rename_on.get() and self.rename_base.get().strip():
            ordered=sorted([r for r in self.rows if r['kind']=='照片'],key=lambda r:(r['target'],r['ts'],r['p'].stem)); counters={}
            for r in ordered:
                key=(r['target'],r['p'].stem); counters.setdefault(r['target'],len({k[1] for k in stems if k[0]==r['target']})+1); stems[key]=stems.get(key,counters[r['target']]); counters[r['target']]=max(counters[r['target']],stems[key]+1)
                r['output_name']=f'{safe(self.rename_base.get())}_{stems[key]:04d}{r["p"].suffix.lower()}'
        self.copy.set(self.copy_mode.get()); super().run(out)

if __name__=='__main__':
    import tkinter.simpledialog
    FullApp().mainloop()
