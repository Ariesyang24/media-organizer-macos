import threading, tkinter as tk, tkinter.simpledialog
from pathlib import Path
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from media_organizer_windows_final import FinalApp
from media_organizer_windows import App, sha
from recognition_engine import analyze,group as quality_group
from face_engine_windows import WindowsFaceEngine,cluster as face_cluster

class Batch2App(FinalApp):
    def __init__(self):
        super().__init__();TkinterDnD._require(self);self.smart=tk.BooleanVar(value=True);self.faces_on=tk.BooleanVar(value=True)
        self.src_box.drop_target_register(DND_FILES);self.src_box.dnd_bind('<<Drop>>',self.drop_src);self.exc_box.drop_target_register(DND_FILES);self.exc_box.dnd_bind('<<Drop>>',self.drop_exc)
        self.tree.configure(columns=('file','date','place','device','kind','quality','duplicate','burst','people','recommend','target'))
        for c,n,w in zip(self.tree['columns'],['文件','日期','地点','设备','类型','质量','重复组','连拍组','人物','建议','目标路径'],[120,75,85,115,42,100,75,65,120,75,270]):self.tree.heading(c,text=n);self.tree.column(c,width=w,anchor='w')
        options=ttk.Frame(self.preview);options.pack(fill='x',padx=10,pady=3,before=self.tree);ttk.Checkbutton(options,text='画质/重复/连拍识别',variable=self.smart).pack(side='left');ttk.Checkbutton(options,text='离线人脸与人物聚类',variable=self.faces_on).pack(side='left',padx=12);ttk.Button(options,text='给选中人物组命名',command=self.name_person).pack(side='right')
        self.status.set('第二批：智能画质识别 + 完全离线人物聚类；可拖入测试文件夹')
    def paths(self,e):return [Path(x) for x in self.tk.splitlist(e.data)]
    def drop_src(self,e):
        n=0
        for p in self.paths(e):
            if p.is_dir() and p not in self.sources:self.sources.append(p);self.src_box.insert('end',str(p));n+=1
        self.status.set(f'拖放添加 {n} 个来源');return e.action
    def drop_exc(self,e):
        n=0
        for p in self.paths(e):
            if p.is_dir() and p not in self.excludes:self.excludes.append(p);self.exc_box.insert('end',str(p));n+=1
        return e.action
    def scan(self):
        App.scan(self)
        if self.stop.is_set():return
        face_engine=WindowsFaceEngine(Path(__file__).parent/'test-results'/'faces.db') if self.faces_on.get() else None
        for i,r in enumerate(self.rows,1):
            if self.stop.is_set():break
            try:
                if self.smart.get():
                    exact=sha(r['p']);r['analysis']=analyze(r['p'],r['kind'],exact);r['analysis']['exact']=exact;m=r['analysis'].get('meta',{});r['dev']=m.get('camera') or r['dev']
                if face_engine and r['kind']=='照片':r['faces']=face_engine.extract(r['p'])
            except Exception as exc:r['recognition_error']=str(exc);r.setdefault('analysis',{'valid':False,'exposure':'识别失败','quality':-1})
            self.update(i,len(self.rows),f'第二批识别 {i}/{len(self.rows)}：{r["p"].name}')
        if self.smart.get():quality_group(self.rows)
        if face_engine:
            faces,people=face_cluster(self.rows);face_engine.close();self.status.set(f'人物识别完成：{faces} 张人脸，{people} 个人物组')
        self.after(0,self.render)
    def render(self):
        self.calculate();self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(self.rows):
            a=r.get('analysis',{});quality='损坏' if not a.get('valid',True) else (f'{a.get("exposure","")} 清晰{a.get("blur",0):.0f}' if a else '未分析')
            self.tree.insert('', 'end',iid=str(i),values=(r['p'].name,r['date'],r['place'],r['dev'],r['kind'],quality,r.get('duplicate',''),r.get('burst',''),r.get('people_text','无人脸'),r.get('recommend',''),r['target']))
        photos=sum(r['kind']=='照片' for r in self.rows);bad=sum(not r.get('analysis',{}).get('valid',True) for r in self.rows);self.stats[0].set(f'{len(self.rows)}\n全部');self.stats[1].set(f'{photos}\n照片');self.stats[2].set(f'{len(self.rows)-photos}\n视频');self.stats[3].set(f'{bad}\n失败/跳过');self.book.select(self.preview);self.action.configure(text='执行整理',command=self.start_run)
    def name_person(self):
        selected=[self.rows[int(x)] for x in self.tree.selection()]
        labels=sorted({p for r in selected for p in r.get('people',set())})
        if not labels:return
        old=labels[0];new=tk.simpledialog.askstring('人物命名',f'将“{old}”命名为：',parent=self)
        if not new:return
        for r in self.rows:
            if old in r.get('people',set()):r['people'].remove(old);r['people'].add(new);r['people_text']='、'.join(sorted(r['people']))
        self.render()

Batch2App().mainloop()
