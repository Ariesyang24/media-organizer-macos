from pathlib import Path

namespace={}
source=Path(__file__).with_name('batch3_media_organizer.pyw').read_text(encoding='utf-8')
source=source.rsplit('Batch3App().mainloop()',1)[0]
exec(compile(source,'batch3_media_organizer.pyw','exec'),namespace)
Batch3App=namespace['Batch3App']

def video_recommendation(result):
    if not result:return '视频待分析'
    if not result.get('valid'):return '无法解码'
    if result.get('duration',0)<1:return '视频过短'
    if result.get('blur',999)<20:return '可能模糊'
    if '严重' in result.get('exposure',''):return '曝光检查'
    return '视频正常'

class FixedApp(Batch3App):
    def scan(self):
        Batch3App.scan(self)
        for row in self.rows:
            if row['kind']=='视频':row['recommend']=video_recommendation(row.get('video_analysis'))
        self.after(0,self.render)
        photo_review=sum(r['kind']=='照片' and r.get('recommend')=='建议检查' for r in self.rows)
        video_review=sum(r['kind']=='视频' and r.get('recommend') not in {'视频正常'} for r in self.rows)
        self.update(len(self.rows),len(self.rows),f'识别完成：图片建议检查 {photo_review}，视频建议检查 {video_review}')
    def render(self):
        Batch3App.render(self)
        invalid=0
        for index,row in enumerate(self.rows):
            if row['kind']=='视频':
                row['recommend']=video_recommendation(row.get('video_analysis'))
                if self.tree.exists(str(index)):self.tree.set(str(index),'recommend',row['recommend'])
                invalid+=row['recommend']=='无法解码'
            elif not row.get('analysis',{}).get('valid',True):invalid+=1
        self.stats[3].set(f'{invalid}\n失败/跳过')

FixedApp().mainloop()
