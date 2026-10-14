from audit_folder_tree_v41 import AuditFolderTreeV41
from v3_ui_components import COLORS
from svg_icon_system import draw_svg_icon
import time


class LockedFolderTreeV45(AuditFolderTreeV41):
    def render(self):
        # Defer expensive full-tree redraws while the application sidebar is
        # changing width. Several independent layout callbacks request a
        # refresh during that short interval; drawing each one caused flashing.
        if time.monotonic() < getattr(self.app, '_sidebar_transition_until', 0):
            self._schedule_resize_render()
            return
        c=self.canvas;c.delete('all');self.items=[];w=max(220,c.winfo_width());y=0;rows=self.app.rows
        colors={'folder':COLORS['blue'],'photo':'#159CC4','video':'#6C4DE6','warning':COLORS['warning'],'check':'#19A477','help':'#E7A23B'}
        audit=[('自动通过','check',sum(r.get('audit_status')=='自动通过' for r in rows),'审核:自动通过'),
               ('待确认','help',sum(r.get('audit_status')=='待确认' for r in rows),'审核:待确认'),
               ('明显问题','warning',sum(r.get('audit_status')=='明显问题' for r in rows),'审核:明显问题'),
               ('文件异常','warning',sum(r.get('audit_status')=='文件异常' for r in rows),'审核:文件异常')]
        material=[('全部素材','folder',len(rows),'全部'),('照片','photo',sum(r.get('kind')=='照片' for r in rows),'照片'),('视频','video',sum(r.get('kind')=='视频' for r in rows),'视频')]
        for title,group in (('审核队列',audit),('素材类型',material)):
            c.create_text(8,y+16,text=title,anchor='w',fill='#17213C',font=('Segoe UI Semibold',11));y+=32
            for label,icon,count,category in group:
                self._row(y,('smart',category),label,'',count,0,False,False,icon,colors[icon],w);y+=self.ROW_H
            y+=6
        c.create_text(8,y+18,text='自定义分类',anchor='w',fill='#17213C',font=('Segoe UI Semibold',11));custom=sum(len(v) for v in self.groups.values());self._badge(w-45,y+18,custom,False);draw_svg_icon(c,'chevron-right',w-18,y+18,14,COLORS['muted'],2);y+=40
        tree=self._flatten(self._tree())
        if not tree:c.create_text(18,y+20,text='暂无自定义文件夹',anchor='w',fill=COLORS['muted'],font=('Segoe UI',9));y+=44
        for item in tree:self._row(y,item['key'],item['label'],item['path'],item['count'],item['depth'],item['children'],item['favorite'],'folder','#F2B735',w,item['target']);y+=self.ROW_H
        c.configure(scrollregion=(0,0,w,max(y+8,c.winfo_height())))
