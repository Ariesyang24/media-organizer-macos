import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from video_engine import analyze_video

batch2_path=Path(__file__).with_name('batch2_media_organizer.pyw')
namespace={'__file__':str(batch2_path)}
source=batch2_path.read_text(encoding='utf-8')
source=source.rsplit('Batch2App().mainloop()',1)[0]
exec(compile(source,'batch2_media_organizer.pyw','exec'),namespace)
Batch2App=namespace['Batch2App']

class Batch3App(Batch2App):
    def __init__(self):
        super().__init__();self.video_on=tk.BooleanVar(value=True)
        columns=tuple(self.tree['columns'])+('video',);self.tree.configure(columns=columns);self.tree.heading('video',text='视频分析');self.tree.column('video',width=210,anchor='w')
        row=ttk.Frame(self.preview);row.pack(fill='x',padx=10,pady=2,before=self.tree);ttk.Checkbutton(row,text='视频镜头/关键帧/画质分析',variable=self.video_on).pack(side='left');ttk.Button(row,text='打开选中视频关键帧',command=self.open_keyframes).pack(side='right')
        self.status.set('第三批：画质、重复、人物聚类 + 视频镜头与关键帧分析')
    def start_side_analysis(self):
        if not self.video_on.get() or self.stop.is_set():return None
        videos=[r for r in self.rows if r['kind']=='视频']
        if not videos:return None
        cache=Path(__file__).parent/'test-results'/'video-keyframes';workers=min(2,len(videos))
        pool=ThreadPoolExecutor(max_workers=workers,thread_name_prefix='video-analysis')
        pending={pool.submit(analyze_video,r['p'],cache):r for r in videos}
        return pool,pending,videos
    def finish_side_analysis(self,side_work):
        if not side_work:return
        pool,pending,videos=side_work
        try:
            for i,future in enumerate(as_completed(pending),1):
                r=pending[future]
                try:r['video_analysis']=future.result()
                except Exception as exc:r['video_analysis']={'valid':False,'error':str(exc)}
                if self.stop.is_set():
                    for job in pending:job.cancel()
                    break
                self.update(i,len(videos),f'图片与视频并行识别 · 视频 {i}/{len(videos)}：{r["p"].name}')
        finally:pool.shutdown(wait=True,cancel_futures=self.stop.is_set())
        self.update(len(videos),len(videos),f'图片与视频并行识别完成：{len(videos)} 个视频')
    def scan(self):
        Batch2App.scan(self)
    def render(self):
        Batch2App.render(self)
        for i,r in enumerate(self.rows):
            v=r.get('video_analysis');text=''
            if v:text=('无法读取：'+v.get('error','')) if not v.get('valid') else f'{v.get("duration",0):.1f}s / {v.get("scenes",0)}镜头 / {v.get("exposure")} / {v.get("visual")}'
            if self.tree.exists(str(i)):self.tree.set(str(i),'video',text)
    def open_keyframes(self):
        for item in self.tree.selection():
            frames=self.rows[int(item)].get('video_analysis',{}).get('keyframes',[])
            if frames:os.startfile(str(Path(frames[0]).parent));return

Batch3App().mainloop()
