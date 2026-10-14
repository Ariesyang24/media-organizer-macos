import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import ttk
from v3_ui_components import COLORS, CanvasButton, Tooltip, rounded_rectangle
from svg_icon_system import draw_svg_icon

class FolderTreePanel(tk.Frame):
    ROW_H = 40
    INDENT = 24
    def __init__(self, master, app, **kwargs):
        super().__init__(master, bg='white', **kwargs)
        self.app=app; self.expanded=set(); self.favorites=set(); self.selected_key=('smart','全部'); self.hover_key=None; self.drop_key=None
        self.query=tk.StringVar(); self.favorites_only=False; self.items=[]; self.groups={}; self.tooltip=None
        self._resize_render_job=None
        header=tk.Frame(self,bg='white'); header.pack(fill='x',pady=(0,10))
        tk.Label(header,text='素材与分类',bg='white',fg='#17213C',font=('Segoe UI Semibold',14)).pack(side='left')
        self.total_badge=tk.Label(header,text='0',bg='#EEF1F7',fg='#27365F',padx=10,pady=3,font=('Segoe UI Semibold',9)); self.total_badge.pack(side='left',padx=10)
        self.add_button=CanvasButton(header,'',icon='add',variant='nav-active',width=38,height=38,command=app.new_folder_for_selection); self.add_button.pack(side='right'); Tooltip(self.add_button,'新建分类')
        refresh=CanvasButton(header,'',icon='rescan',width=38,height=38,command=app.refresh_sidebar); refresh.pack(side='right',padx=(0,7)); Tooltip(refresh,'刷新目录')
        search=tk.Frame(self,bg='white',highlightthickness=1,highlightbackground=COLORS['border']); search.pack(fill='x',pady=(0,10))
        from svg_icon_system import SvgIcon
        SvgIcon(search,'search',COLORS['muted'],'white',size=34,icon_size=19).pack(side='left',padx=(4,0))
        entry=tk.Entry(search,textvariable=self.query,relief='flat',bd=0,font=('Segoe UI',10),fg=COLORS['text']); entry.pack(side='left',fill='x',expand=True,ipady=9)
        entry.bind('<KeyRelease>',lambda _e:self.render())
        self.filter_button=CanvasButton(search,'',icon='filter',width=38,height=38,command=self.toggle_favorites); self.filter_button.pack(side='right',padx=3); Tooltip(self.filter_button,'仅显示收藏')
        area=tk.Frame(self,bg='white'); area.pack(fill='both',expand=True)
        style=ttk.Style(); style.configure('Slim.Vertical.TScrollbar',arrowsize=0,width=8,troughcolor='#F2F4F8',background='#C8CFDC',borderwidth=0)
        self.canvas=tk.Canvas(area,bg='white',highlightthickness=0,bd=0,yscrollincrement=self.ROW_H)
        self.scroll=ttk.Scrollbar(area,orient='vertical',style='Slim.Vertical.TScrollbar',command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll.set); self.canvas.pack(side='left',fill='both',expand=True); self.scroll.pack(side='right',fill='y')
        # A sidebar resize emits a burst of Configure events. Rendering the
        # complete category tree for every event caused the panel to visibly
        # flash and made the expand button feel unstable.
        self.canvas.bind('<Configure>',self._schedule_resize_render); self.canvas.bind('<MouseWheel>',self.on_wheel); self.canvas.bind('<Motion>',self.on_motion); self.canvas.bind('<Leave>',self.on_leave); self.canvas.bind('<ButtonRelease-1>',self.on_click)
        footer=tk.Frame(self,bg='white',highlightthickness=1,highlightbackground=COLORS['border']); footer.pack(fill='x',pady=(8,0))
        self.selected_text=tk.StringVar(value='拖动所选素材到左侧分类'); tk.Label(footer,textvariable=self.selected_text,bg='white',fg=COLORS['blue'],font=('Segoe UI',8),wraplength=280,justify='left').pack(side='left',padx=8,pady=8)

    def _schedule_resize_render(self, _event=None):
        if self._resize_render_job is not None:
            try:self.after_cancel(self._resize_render_job)
            except tk.TclError:pass
        self._resize_render_job=self.after(45,self._render_after_resize)

    def _render_after_resize(self):
        self._resize_render_job=None
        if self.winfo_exists():self.render()

    def toggle_favorites(self):
        self.favorites_only=not self.favorites_only; self.filter_button.configure(variant='nav-active' if self.favorites_only else 'secondary'); self.render()
    def on_wheel(self,e): self.canvas.yview_scroll(-1 if e.delta>0 else 1,'units'); return 'break'
    def set_data(self, groups):
        self.groups=dict(groups); self.total_badge.configure(text=str(len(groups))); self.render()
    def _smart(self):
        rows=self.app.rows; failed=sum(not r.get('analysis',{}).get('valid',True) or r.get('recommend')=='无法解码' for r in rows)
        audit=[('自动通过','check',sum(r.get('audit_status')=='自动通过' for r in rows),'审核:自动通过'),('待确认','help',sum(r.get('audit_status')=='待确认' for r in rows),'审核:待确认'),('明显问题','warning',sum(r.get('audit_status')=='明显问题' for r in rows),'审核:明显问题'),('文件异常','warning',failed,'审核:文件异常')]
        material=[('全部素材','folder',len(rows),'全部'),('照片','photo',sum(r.get('kind')=='照片' for r in rows),'照片'),('视频','video',sum(r.get('kind')=='视频' for r in rows),'视频')]
        return audit,material
    def _tree(self):
        root={}
        try: base=Path(self.app.out.get()).resolve()
        except Exception: base=None
        for target,rows in self.groups.items():
            p=Path(target)
            try: parts=p.resolve().relative_to(base).parts if base else p.parts[-2:]
            except Exception: parts=p.parts[-2:]
            node=root; partial=[]
            for part in parts:
                partial.append(part); node=node.setdefault(part,{'_children':{},'_path':str(p) if len(partial)==len(parts) else '', '_count':0}); node['_count']+=len(rows); node=node['_children']
        return root
    def _flatten(self,node,depth=0,parent=''):
        out=[]; q=self.query.get().strip().lower()
        for name,data in sorted(node.items(),key=lambda x:x[0].lower()):
            key=('folder',data['_path'] or parent+'/'+name); full=data['_path'] or key[1]; children=data['_children']; favorite=full in self.favorites
            visible=(not q or q in name.lower() or q in full.lower()) and (not self.favorites_only or favorite)
            child_rows=self._flatten(children,depth+1,full) if (key in self.expanded or q) else []
            if visible or child_rows: out.append({'key':key,'label':name,'path':full,'count':data['_count'],'depth':depth,'children':bool(children),'favorite':favorite,'target':data['_path']}); out.extend(child_rows)
        return out
    def render(self):
        c=self.canvas; c.delete('all'); self.items=[]; w=max(260,c.winfo_width()); y=0
        colors={'folder':COLORS['blue'],'photo':'#159CC4','video':'#6C4DE6','warning':COLORS['warning'],'check':'#19A477','help':'#E7A23B'}
        audit,material=self._smart();c.create_text(8,16,text='审核队列',anchor='w',fill='#17213C',font=('Segoe UI Semibold',11));y=32
        for label,icon,count,category in audit:
            key=('smart',category); self._row(y,key,label,'',count,0,False,False,icon,colors[icon],w); y+=self.ROW_H
        y+=6;c.create_text(8,y+16,text='素材类型',anchor='w',fill='#17213C',font=('Segoe UI Semibold',11));y+=32
        for label,icon,count,category in material:
            key=('smart',category); self._row(y,key,label,'',count,0,False,False,icon,colors[icon],w); y+=self.ROW_H
        y+=10; c.create_text(8,y+18,text='自定义分类',anchor='w',fill='#17213C',font=('Segoe UI Semibold',11)); custom=sum(len(v) for v in self.groups.values()); self._badge(w-45,y+18,custom,False); draw_svg_icon(c,'chevron-right',w-18,y+18,14,COLORS['muted'],2); y+=40
        tree=self._flatten(self._tree())
        if not tree:
            c.create_text(18,y+20,text='暂无自定义文件夹',anchor='w',fill=COLORS['muted'],font=('Segoe UI',9)); y+=44
        for item in tree:
            self._row(y,item['key'],item['label'],item['path'],item['count'],item['depth'],item['children'],item['favorite'],'folder','#F2B735',w,item['target']); y+=self.ROW_H
        c.configure(scrollregion=(0,0,w,max(y+8,c.winfo_height())))
    def _row(self,y,key,label,path,count,depth,children,favorite,icon,color,w,target=''):
        selected=key==self.selected_key; hover=key==self.hover_key; drop=key==self.drop_key; fill='#E9EEFF' if (selected or drop) else ('#F5F7FB' if hover else 'white')
        c=self.canvas; c.create_rectangle(2,y,w-3,y+self.ROW_H,fill=fill,outline=COLORS['blue'] if drop else '',width=2 if drop else 1,tags=('row',));
        if selected:c.create_rectangle(2,y,5,y+self.ROW_H,fill=COLORS['blue'],outline='')
        x=14+depth*self.INDENT
        if children: draw_svg_icon(c,'chevron-right' if key not in self.expanded else 'chevron-left',x+7,y+20,13,'#27365F',2)
        if key[0]=='folder':
            draw_svg_icon(c,'star-fill' if favorite else 'star',x+31,y+20,18,'#405793' if favorite else '#8992A3',2); ix=x+56
        else: ix=x+12
        draw_svg_icon(c,icon,ix,y+20,20,color,2); tx=ix+27
        custom=key[0]=='folder' and '自定义分类' in Path(target or path or '').parts
        font=tkfont.Font(family='Segoe UI',size=9,weight='bold' if selected else 'normal'); maxw=max(40,w-tx-(98 if custom else 68)); shown=label
        while font.measure(shown)>maxw and len(shown)>2: shown=shown[:-2]+'…'
        c.create_text(tx,y+20,text=shown,anchor='w',fill='#17213C',font=font); self._badge(w-31,y+20,count,key==('smart','文件异常'))
        if custom: draw_svg_icon(c,'more',w-66,y+20,17,COLORS['muted'],2)
        self.items.append({'y1':y,'y2':y+self.ROW_H,'key':key,'path':path or label,'count':count,'depth':depth,'children':children,'star_x':x+18 if key[0]=='folder' else -1,'more_x':w-66 if custom else -1,'target':target,'category':key[1] if key[0]=='smart' else ''})
    def _badge(self,x,y,value,danger=False):
        text=str(value); width=max(34,16+len(text)*7); rounded_rectangle(self.canvas,x-width/2,y-13,x+width/2,y+13,13,fill='#FFE9E9' if danger else '#EEF1F7',outline=''); self.canvas.create_text(x,y,text=text,fill=COLORS['warning'] if danger else '#27365F',font=('Segoe UI Semibold',8))
    def _at(self,y):
        yy=self.canvas.canvasy(y); return next((i for i in self.items if i['y1']<=yy<i['y2']),None)
    def on_click(self,e):
        item=self._at(e.y)
        if not item:return
        yy=self.canvas.canvasy(e.y); x=e.x; key=item['key']
        if key[0]=='folder' and item.get('more_x',-1)-18<=x<=item.get('more_x',-1)+18:
            feature=getattr(self.app,'classification_pagination_v49',None)
            if feature: feature.category_menu_at(item,e.x_root,e.y_root)
            return
        if key[0]=='folder' and item['star_x']-12<=x<=item['star_x']+22:
            path=item['path']; self.favorites.discard(path) if path in self.favorites else self.favorites.add(path); self.render(); return
        if item['children'] and x<45+(key[0]=='folder')*60:
            self.expanded.discard(key) if key in self.expanded else self.expanded.add(key); self.render(); return
        self.selected_key=key; self.selected_text.set('已选择 1 个文件夹')
        if key[0]=='smart': self.app.open_category(item['category'])
        elif item['target']: self.app.select_folder_target(item['target'])
        self.render()
    def on_motion(self,e):
        item=self._at(e.y); key=item['key'] if item else None
        if key!=self.hover_key: self.hover_key=key; self.render()
        if self.tooltip: self.tooltip.destroy(); self.tooltip=None
        if item and item['path'] and len(item['path'])>28:
            self.tooltip=tk.Toplevel(self); self.tooltip.overrideredirect(True); self.tooltip.attributes('-topmost',True); self.tooltip.geometry(f'+{e.x_root+12}+{e.y_root+12}'); tk.Label(self.tooltip,text=item['path'],bg=COLORS['text'],fg='white',padx=8,pady=4,font=('Segoe UI',8)).pack()
    def on_leave(self,_e):
        self.hover_key=None
        if self.tooltip:self.tooltip.destroy();self.tooltip=None
        self.render()
