import csv, hashlib, os, re, shutil, threading, uuid
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
try:
    from PIL import Image, ExifTags
except ImportError: Image=ExifTags=None

PHOTOS={'.jpg','.jpeg','.png','.heic','.tif','.tiff','.dng','.cr2','.cr3','.nef','.arw','.raf','.rw2','.orf'}
VIDEOS={'.mp4','.mov','.m4v','.avi','.mkv','.mts','.m2ts','.wmv','.webm'}
EVENT=re.compile(r'(20\d{2})[.\-_年](\d{1,2})[.\-_月](\d{1,2})日?[ _.-]*(.*)')
BAD=re.compile(r'[\\/:*?"<>|\r\n]+')
def safe(s): return BAD.sub('-',s).strip().rstrip('.') or '未知'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        while b:=f.read(1048576): h.update(b)
    return h.hexdigest()
def meta(p):
    ts=p.stat().st_mtime; day=datetime.fromtimestamp(ts).strftime('%Y-%m-%d'); dev='未知设备'
    if Image and p.suffix.lower() in PHOTOS:
        try:
            with Image.open(p) as im:
                ex={ExifTags.TAGS.get(k,k):v for k,v in im.getexif().items()}; dt=ex.get('DateTimeOriginal') or ex.get('DateTime')
                if dt:
                    d=datetime.strptime(str(dt),'%Y:%m:%d %H:%M:%S'); ts=d.timestamp(); day=d.strftime('%Y-%m-%d')
                make=str(ex.get('Make','')).strip(); model=str(ex.get('Model','')).strip(); dev=' '.join(dict.fromkeys(x for x in (make,model) if x)) or dev
        except Exception: pass
    return day,ts,dev
def folder_event(p,root):
    cur=p.parent
    while True:
        m=EVENT.search(cur.name)
        if m and m.group(4).strip(' _.-'):
            try: return datetime(*map(int,m.groups()[:3])).strftime('%Y-%m-%d'),m.group(4).strip(' _.-')
            except ValueError: pass
        if cur==root or cur.parent==cur: return None
        cur=cur.parent

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('素材整理工具 · Windows'); self.geometry('1200x720')
        self.sources=[]; self.excludes=[]; self.rows=[]; self.stop=threading.Event(); self.out=tk.StringVar(value=str(Path.home()/'Pictures'/'所有素材')); self.status=tk.StringVar(value='添加来源后扫描'); self.place=tk.StringVar()
        bar=ttk.Frame(self,padding=10); bar.pack(fill='x')
        for n,c in [('添加来源',self.add),('添加排除目录',self.exclude),('选择输出',self.output),('扫描并预览',self.start_scan),('执行整理',self.start_run),('安全停止',self.stop.set)]: ttk.Button(bar,text=n,command=c).pack(side='left',padx=3)
        ttk.Label(bar,text='输出：').pack(side='left',padx=(15,0)); ttk.Entry(bar,textvariable=self.out).pack(side='left',fill='x',expand=True)
        edit=ttk.Frame(self,padding=(10,0,10,8)); edit.pack(fill='x'); ttk.Label(edit,text='选中行地点：').pack(side='left'); ttk.Entry(edit,textvariable=self.place,width=22).pack(side='left'); ttk.Button(edit,text='应用',command=self.apply_place).pack(side='left',padx=5)
        cols=('file','date','place','device','kind','target'); self.tree=ttk.Treeview(self,columns=cols,show='headings',selectmode='extended')
        for c,n,w in zip(cols,['文件','日期','地点','设备','类型','目标目录'],[180,90,120,180,60,480]): self.tree.heading(c,text=n); self.tree.column(c,width=w,anchor='w')
        self.tree.pack(fill='both',expand=True,padx=10); self.progress=ttk.Progressbar(self); self.progress.pack(fill='x',padx=10,pady=6); ttk.Label(self,textvariable=self.status,padding=10).pack(fill='x')
    def add(self):
        if x:=filedialog.askdirectory(title='选择素材来源'): self.sources.append(Path(x)); self.status.set(f'已添加来源：{x}')
    def exclude(self):
        if x:=filedialog.askdirectory(title='选择排除目录'): self.excludes.append(Path(x)); self.status.set(f'已排除：{x}')
    def output(self):
        if x:=filedialog.askdirectory(title='选择总素材文件夹'): self.out.set(x)
    def update(self,n,total,text): self.after(0,lambda:(self.progress.configure(maximum=max(1,total),value=n),self.status.set(text)))
    def start_scan(self):
        if not self.sources: return messagebox.showwarning('提示','请先添加素材来源')
        self.stop.clear(); threading.Thread(target=self.scan,daemon=True).start()
    def scan(self):
        files=[]; blocked=[os.path.normcase(str(x.resolve())) for x in self.excludes+[Path(self.out.get())]]
        for root in self.sources:
            for d,dirs,names in os.walk(root):
                dirs[:]=[x for x in dirs if not any(os.path.normcase(str((Path(d)/x).resolve())).startswith(b) for b in blocked)]
                files += [(Path(d)/n,root) for n in names if (Path(n).suffix.lower() in PHOTOS|VIDEOS)]
        rows=[]
        for i,(p,root) in enumerate(files,1):
            if self.stop.is_set(): break
            day,ts,dev=meta(p); event=folder_event(p,root); place=event[1] if event else '未设置'; day=event[0] if event else day; kind='照片' if p.suffix.lower() in PHOTOS else '视频'; target=str(Path(f'{day.replace("-",".")} {safe(place)}')/f'{safe(dev)} {kind}')
            rows.append({'p':p,'date':day,'ts':ts,'place':place,'dev':dev,'kind':kind,'target':target}); self.update(i,len(files),f'扫描 {i}/{len(files)}：{p.name}')
        self.rows=rows; self.after(0,self.render); self.update(len(rows),len(files),f'扫描完成：{len(rows)} 个文件')
    def render(self):
        self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(self.rows): self.tree.insert('', 'end',iid=str(i),values=(r['p'].name,r['date'],r['place'],r['dev'],r['kind'],r['target']))
    def apply_place(self):
        v=self.place.get().strip()
        for x in self.tree.selection():
            r=self.rows[int(x)]; r['place']=v; r['target']=str(Path(f'{r["date"].replace("-",".")} {safe(v)}')/f'{safe(r["dev"])} {r["kind"]}')
        self.render()
    def start_run(self):
        if not self.rows: return messagebox.showwarning('提示','请先扫描并检查预览')
        if messagebox.askyesno('确认',f'复制并校验 {len(self.rows)} 个文件到：\n{self.out.get()}'): self.stop.clear(); threading.Thread(target=self.run,daemon=True).start()
    def run(self):
        out=Path(self.out.get()); done=[]; failed=[]
        for i,r in enumerate(self.rows,1):
            if self.stop.is_set(): break
            try:
                folder=out/r['target']; folder.mkdir(parents=True,exist_ok=True); s=sha(r['p']); dst=folder/r['p'].name; n=2
                while dst.exists() and sha(dst)!=s: dst=folder/f'{r["p"].stem}_{n}{r["p"].suffix}'; n+=1
                if not dst.exists():
                    part=dst.with_name(f'.{dst.name}.partial-{uuid.uuid4().hex}'); shutil.copy2(r['p'],part)
                    if sha(part)!=s: raise IOError('SHA-256 校验失败')
                    os.replace(part,dst)
                done.append((r,dst,s))
            except Exception as e: failed.append(f'{r["p"]}: {e}')
            self.update(i,len(self.rows),f'整理 {i}/{len(self.rows)}')
        stamp=datetime.now().strftime('%Y%m%d_%H%M%S'); report=out/f'整理记录_{stamp}.csv'; out.mkdir(parents=True,exist_ok=True)
        with report.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f); w.writerow(['FileName','OriginalPath','CaptureDate','Device','Location','TargetPath','SHA256']); [w.writerow([r['p'].name,r['p'],r['date'],r['dev'],r['place'],d,s]) for r,d,s in done]
        if failed: (out/f'整理失败_{stamp}.txt').write_text('\n'.join(failed),encoding='utf-8')
        self.update(len(done),len(self.rows),f'完成：成功 {len(done)}，失败 {len(failed)}；{report}')
if __name__=='__main__': App().mainloop()
