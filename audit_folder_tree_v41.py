import tkinter as tk
import tkinter.font as tkfont
from folder_tree_panel import FolderTreePanel
from v3_ui_components import COLORS
from svg_icon_system import draw_svg_icon


class AuditFolderTreeV41(FolderTreePanel):
    def _groups(self):
        rows=self.app.rows
        audit=[('自动通过','check',sum(r.get('audit_status')=='自动通过' for r in rows),'审核:自动通过'),
               ('待确认','help',sum(r.get('audit_status')=='待确认' for r in rows),'审核:待确认'),
               ('明显问题','warning',sum(r.get('audit_status')=='明显问题' for r in rows),'审核:明显问题'),
               ('文件异常','warning',sum(r.get('audit_status')=='文件异常' for r in rows),'审核:文件异常')]
        tags=[('白底正常','photo',sum(r.get('audit_result')=='白底正常' for r in rows),'标签:白底正常'),
              ('疑似过曝','warning',sum('过曝' in str((r.get('analysis') or {}).get('exposure','')) for r in rows),'标签:疑似过曝'),
              ('主体偏亮','help',sum(r.get('audit_result')=='主体偏亮' for r in rows),'标签:主体偏亮'),
              ('模糊','help',sum(float((r.get('analysis') or {}).get('quality') or 0)<25 for r in rows),'标签:模糊'),
              ('重复','duplicate',sum(bool(r.get('duplicate')) for r in rows),'标签:重复'),
              ('连拍','batch',sum(bool(r.get('burst')) for r in rows),'标签:连拍')]
        material=[('全部素材','folder',len(rows),'全部'),('照片','photo',sum(r.get('kind')=='照片' for r in rows),'照片'),('视频','video',sum(r.get('kind')=='视频' for r in rows),'视频')]
        return audit,tags,material

    def render(self):
        c=self.canvas;c.delete('all');self.items=[];w=max(220,c.winfo_width());y=0
        colors={'folder':COLORS['blue'],'photo':'#159CC4','video':'#6C4DE6','warning':COLORS['warning'],'check':'#19A477','help':'#E7A23B','duplicate':'#6C4DE6','batch':'#4263EB'}
        audit,tags,material=self._groups()
        for title,rows in (('审核队列',audit),('分析标签',tags),('素材类型',material)):
            c.create_text(8,y+16,text=title,anchor='w',fill='#17213C',font=('Segoe UI Semibold',11));y+=32
            for label,icon,count,category in rows:
                key=('smart',category);self._row(y,key,label,'',count,0,False,False,icon,colors[icon],w);y+=self.ROW_H
            y+=6
        c.create_text(8,y+18,text='自定义分类',anchor='w',fill='#17213C',font=('Segoe UI Semibold',11));custom=sum(len(v) for v in self.groups.values());self._badge(w-45,y+18,custom,False);draw_svg_icon(c,'chevron-right',w-18,y+18,14,COLORS['muted'],2);y+=40
        tree=self._flatten(self._tree())
        if not tree:c.create_text(18,y+20,text='暂无自定义文件夹',anchor='w',fill=COLORS['muted'],font=('Segoe UI',9));y+=44
        for item in tree:self._row(y,item['key'],item['label'],item['path'],item['count'],item['depth'],item['children'],item['favorite'],'folder','#F2B735',w,item['target']);y+=self.ROW_H
        c.configure(scrollregion=(0,0,w,max(y+8,c.winfo_height())))
