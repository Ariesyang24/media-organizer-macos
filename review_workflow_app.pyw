import csv, os
from datetime import datetime
from pathlib import Path

namespace={}
source=Path(__file__).with_name('batch3_fixed_recommendations.pyw').read_text(encoding='utf-8')
source=source.rsplit('FixedApp().mainloop()',1)[0]
exec(compile(source,'batch3_fixed_recommendations.pyw','exec'),namespace)
FixedApp=namespace['FixedApp']

class ReviewApp(FixedApp):
    def __init__(self):
        super().__init__();self.filter_var=tk.StringVar(value='全部');self.search_var=tk.StringVar();self.excluded=[]
        panel=ttk.LabelFrame(self.preview,text='识别结果审核',padding=7);panel.pack(fill='x',padx=8,pady=4,before=self.tree)
        ttk.Label(panel,text='筛选：').pack(side='left');box=ttk.Combobox(panel,textvariable=self.filter_var,state='readonly',width=14,values=['全部','图片建议检查','视频建议检查','完全/近似重复','连拍素材','检测到人物','无法解码']);box.pack(side='left');box.bind('<<ComboboxSelected>>',lambda e:self.apply_filter())
        ttk.Label(panel,text='搜索：').pack(side='left',padx=(12,2));entry=ttk.Entry(panel,textvariable=self.search_var,width=24);entry.pack(side='left');entry.bind('<KeyRelease>',lambda e:self.apply_filter())
        ttk.Button(panel,text='打开原文件',command=self.open_original).pack(side='right');ttk.Button(panel,text='排除选中',command=self.exclude_selected).pack(side='right',padx=4);ttk.Button(panel,text='导出审核报告',command=self.export_review).pack(side='right')
        self.status.set('识别后：筛选 → 打开核对 → 排除不整理项 → 导出报告 → 执行整理')
    def render(self):
        FixedApp.render(self);self.apply_filter()
    def match(self,row):
        mode=self.filter_var.get();recommend=row.get('recommend','');duplicate=row.get('duplicate','');burst=row.get('burst','');people=row.get('people_text','无人脸')
        rules={'全部':True,'图片建议检查':row['kind']=='照片' and recommend=='建议检查','视频建议检查':row['kind']=='视频' and recommend!='视频正常','完全/近似重复':bool(duplicate),'连拍素材':bool(burst),'检测到人物':people not in {'','无人脸'},'无法解码':recommend=='无法解码'}
        text=self.search_var.get().strip().lower();hay=' '.join([row['p'].name,row.get('dev',''),row.get('place',''),people,recommend]).lower()
        return rules.get(mode,True) and (not text or text in hay)
    def apply_filter(self):
        if not hasattr(self,'tree'):return
        shown=0
        for i,row in enumerate(self.rows):
            item=str(i)
            if self.tree.exists(item) and not self.match(row):self.tree.detach(item)
            elif self.match(row):
                if not self.tree.exists(item):
                    a=row.get('analysis',{});quality='损坏' if not a.get('valid',True) else (f'{a.get("exposure","")} 清晰{a.get("blur",0):.0f}' if a else '未分析');v=row.get('video_analysis');video='' if not v else f'{v.get("duration",0):.1f}s / {v.get("scenes",0)}镜头 / {v.get("exposure")}'
                    self.tree.insert('', 'end',iid=item,values=(row['p'].name,row['date'],row['place'],row['dev'],row['kind'],quality,row.get('duplicate',''),row.get('burst',''),row.get('people_text','无人脸'),row.get('recommend',''),row['target'],video))
                shown+=1
        self.status.set(f'当前显示 {shown}/{len(self.rows)}；可打开原文件核对，排除项不会移动或删除')
    def open_original(self):
        selected=self.tree.selection()
        if selected:os.startfile(str(self.rows[int(selected[0])]['p']))
    def exclude_selected(self):
        indices=sorted((int(x) for x in self.tree.selection()),reverse=True)
        for i in indices:self.excluded.append(self.rows.pop(i))
        self.calculate();self.render();self.status.set(f'已从本次整理计划排除 {len(indices)} 项；原文件未改动')
    def export_review(self):
        folder=Path(__file__).parent/'test-results'/'reviews';folder.mkdir(parents=True,exist_ok=True);path=folder/f'审核报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        with path.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f);w.writerow(['File','Type','Device','Location','Quality','Duplicate','Burst','People','Recommendation','VideoSummary','Target'])
            for r in self.rows:
                a=r.get('analysis',{});v=r.get('video_analysis',{});w.writerow([r['p'],r['kind'],r['dev'],r['place'],f'{a.get("exposure","")} blur={a.get("blur","")}',r.get('duplicate',''),r.get('burst',''),r.get('people_text',''),r.get('recommend',''),f'{v.get("duration","")}s scenes={v.get("scenes","")}',r['target']])
        self.status.set(f'审核报告已导出：{path}')

ReviewApp().mainloop()
