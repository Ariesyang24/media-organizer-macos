import tkinter.simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from media_organizer_windows_final import FinalApp
from media_organizer_windows import App, sha
from recognition_engine import analyze,group

class SmartApp(FinalApp):
    def __init__(self):
        super().__init__();TkinterDnD._require(self);self.analysis_enabled=tk.BooleanVar(value=True);self._analyzing=False
        self.src_box.drop_target_register(DND_FILES);self.src_box.dnd_bind('<<Drop>>',self.drop_sources);self.exc_box.drop_target_register(DND_FILES);self.exc_box.dnd_bind('<<Drop>>',self.drop_exclusions)
        self.tree.configure(columns=('file','date','place','device','kind','quality','duplicate','burst','recommend','target'))
        for c,n,w in zip(self.tree['columns'],['文件','日期','地点','设备','类型','质量识别','重复组','连拍组','建议','目标路径'],[135,80,95,135,45,110,90,75,80,330]):self.tree.heading(c,text=n);self.tree.column(c,width=w,anchor='w')
        ttk.Checkbutton(self.preview,text='扫描时启用智能识别（元数据、损坏、模糊、曝光、重复、连拍）',variable=self.analysis_enabled).pack(anchor='w',padx=12,pady=3,before=self.tree)
        self.status.set('可拖入文件夹；扫描时默认启用第一批智能识别')
    def paths(self,e):return [Path(x) for x in self.tk.splitlist(e.data)]
    def drop_sources(self,e):
        n=0
        for p in self.paths(e):
            if p.is_dir() and p not in self.sources:self.sources.append(p);self.src_box.insert('end',str(p));n+=1
        self.status.set(f'拖放添加 {n} 个来源');return e.action
    def drop_exclusions(self,e):
        n=0
        for p in self.paths(e):
            if p.is_dir() and p not in self.excludes:self.excludes.append(p);self.exc_box.insert('end',str(p));n+=1
        self.status.set(f'拖放添加 {n} 个排除目录');return e.action
    def scan(self):
        App.scan(self)
        if not self.analysis_enabled.get() or self.stop.is_set():return
        self._analyzing=True
        for i,r in enumerate(self.rows,1):
            if self.stop.is_set():break
            try:
                exact=sha(r['p']);a=analyze(r['p'],r['kind'],exact);r['analysis']=a
                m=a.get('meta',{});r['dev']=m.get('camera') or r['dev']
                captured=m.get('captured')
                if captured and str(captured)[:4].isdigit():r['date']=str(captured)[:10].replace(':','-')
            except Exception as exc:r['analysis']={'valid':False,'quality':-1,'exposure':'识别失败'};r['analysis_error']=str(exc)
            self.update(i,len(self.rows),f'智能识别 {i}/{len(self.rows)}：{r["p"].name}')
        group(self.rows);self._analyzing=False;self.after(0,self.render);self.update(len(self.rows),len(self.rows),'智能识别完成：请检查质量、重复、连拍和保留建议')
    def render(self):
        self.calculate();self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(self.rows):
            a=r.get('analysis',{});quality=('损坏' if not a.get('valid',True) else (f'清晰 {a.get("blur",0):.0f} / {a.get("exposure","待识别")}' if a else '待识别'))
            self.tree.insert('', 'end',iid=str(i),values=(r['p'].name,r['date'],r['place'],r['dev'],r['kind'],quality,r.get('duplicate',''),r.get('burst',''),r.get('recommend',''),r['target']))
        photos=sum(r['kind']=='照片' for r in self.rows);bad=sum(not r.get('analysis',{}).get('valid',True) for r in self.rows);self.stats[0].set(f'{len(self.rows)}\n全部');self.stats[1].set(f'{photos}\n照片');self.stats[2].set(f'{len(self.rows)-photos}\n视频');self.stats[3].set(f'{bad}\n失败/跳过');self.book.select(self.preview);self.action.configure(text='执行整理',command=self.start_run)

SmartApp().mainloop()
