import os
from pathlib import Path
from video_engine import analyze_video

namespace={}
source=Path(__file__).with_name('batch2_media_organizer.pyw').read_text(encoding='utf-8')
source=source.rsplit('Batch2App().mainloop()',1)[0]
exec(compile(source,'batch2_media_organizer.pyw','exec'),namespace)
Batch2App=namespace['Batch2App']

class Batch3App(Batch2App):
    def __init__(self):
        super().__init__();self.video_on=tk.BooleanVar(value=True)
        columns=tuple(self.tree['columns'])+('video',);self.tree.configure(columns=columns);self.tree.heading('video',text='视频分析');self.tree.column('video',width=210,anchor='w')
        row=ttk.Frame(self.preview);row.pack(fill='x',padx=10,pady=2,before=self.tree);ttk.Checkbutton(row,text='视频镜头/关键帧/画质分析',variable=self.video_on).pack(side='left');ttk.Button(row,text='打开选中视频关键帧',command=self.open_keyframes).pack(side='right')
        self.status.set('第三批：画质、重复、人物聚类 + 视频镜头与关键帧分析')
    def scan(self):
        Batch2App.scan(self)
        if not self.video_on.get() or self.stop.is_set():return
        videos=[r for r in self.rows if r['kind']=='视频'];cache=Path(__file__).parent/'test-results'/'video-keyframes'
        for i,r in enumerate(videos,1):
            if self.stop.is_set():break
            r['video_analysis']=analyze_video(r['p'],cache);self.update(i,len(videos),f'视频分析 {i}/{len(videos)}：{r["p"].name}')
        self.after(0,self.render);self.update(len(videos),len(videos),f'视频分析完成：{len(videos)} 个视频')
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
