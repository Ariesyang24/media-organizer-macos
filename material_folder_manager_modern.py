import os
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from v3_ui_components import COLORS, CanvasButton, RoundedCard, rounded_rectangle
from svg_icon_system import draw_svg_icon, SvgIcon
from material_folder_manager import save_material_folders, valid_folder_name
from manager_thumbnail_column import ManagerThumbnailColumn

class CategoryCanvas(tk.Canvas):
    ROW=48
    def __init__(self,master,owner,**kw):
        super().__init__(master,bg='white',highlightthickness=0,bd=0,yscrollincrement=self.ROW,**kw);self.owner=owner;self.items=[];self.hover=None
        self.bind('<Configure>',lambda _e:self.redraw());self.bind('<Motion>',self.motion);self.bind('<Leave>',lambda _e:self.leave());self.bind('<ButtonRelease-1>',self.click);self.bind('<MouseWheel>',self.wheel)
    def wheel(self,e):self.yview_scroll(-1 if e.delta>0 else 1,'units');return 'break'
    def redraw(self):
        self.delete('all');self.items=[];w=max(180,self.winfo_width());y=0;q=self.owner.folder_query.get().strip().lower()
        for name in sorted(self.owner.folder_set,key=str.lower):
            if q and q not in name.lower():continue
            count=sum(v==name for v in self.owner.staged.values());selected=name==self.owner.current_folder;hover=name==self.hover;fill='#E9EEFF' if selected else('#F5F7FB' if hover else 'white')
            self.create_rectangle(2,y,w-3,y+self.ROW,fill=fill,outline='');
            if selected:self.create_rectangle(2,y,5,y+self.ROW,fill=COLORS['blue'],outline='')
            draw_svg_icon(self,'folder',20,y+24,20,COLORS['blue'],2);font=tkfont.Font(family='Segoe UI',size=10,weight='bold' if selected else 'normal');shown=name;maxw=w-100
            while font.measure(shown)>maxw and len(shown)>2:shown=shown[:-2]+'…'
            self.create_text(40,y+24,text=shown,anchor='w',fill='#17213C',font=font);bw=max(32,16+len(str(count))*7);rounded_rectangle(self,w-62,y+11,w-62+bw,y+37,13,fill='#EEF1F7',outline='');self.create_text(w-62+bw/2,y+24,text=str(count),fill='#27365F',font=('Segoe UI Semibold',8));draw_svg_icon(self,'more',w-16,y+24,17,COLORS['muted'],2)
            self.items.append((y,y+self.ROW,name));y+=self.ROW
        self.configure(scrollregion=(0,0,w,max(y,self.winfo_height())))
    def at(self,y):
        yy=self.canvasy(y);return next((name for a,b,name in self.items if a<=yy<b),None)
    def click(self,e):
        name=self.at(e.y)
        if name:self.owner.select_folder(name)
    def motion(self,e):
        name=self.at(e.y)
        if name!=self.hover:self.hover=name;self.redraw()
    def leave(self):self.hover=None;self.redraw()

class ModernMaterialFolderManager(tk.Toplevel):
    def __init__(self,app):
        super().__init__(app);self.app=app;self.title('管理分类');self.geometry('1500x900');self.minsize(1180,720);self.configure(bg=COLORS['app_bg']);self.transient(app)
        self.original={i:r.get('custom_folder','') for i,r in enumerate(app.rows)};self.staged=dict(self.original);self.folder_set={v for v in self.staged.values() if v};self.current_folder=next(iter(sorted(self.folder_set)), '')
        self.mode='current';self.undo_stack=[];self.dirty=False;self.target=tk.StringVar(value=self.current_folder);self.folder_query=tk.StringVar();self.file_query=tk.StringVar();self.target_popup=None;self.dragging=False
        self.protocol('WM_DELETE_WINDOW',self.close);self._style();self.build();self.refresh_all()
    def _style(self):
        s=ttk.Style(self);s.configure('ModernManager.Treeview',background='white',fieldbackground='white',foreground=COLORS['text'],rowheight=66,borderwidth=0,font=('Segoe UI',9));s.configure('ModernManager.Treeview.Heading',background='#F7F8FB',foreground=COLORS['muted'],relief='flat',padding=(8,10),font=('Segoe UI Semibold',9));s.map('ModernManager.Treeview',background=[('selected','#E9EEFF')])
    def build(self):
        top=tk.Frame(self,bg=COLORS['app_bg']);top.pack(fill='x',padx=24,pady=(20,14));CanvasButton(top,'',icon='chevron-left',width=44,height=44,command=self.close).pack(side='left',padx=(0,14))
        titles=tk.Frame(top,bg=COLORS['app_bg']);titles.pack(side='left');tk.Label(titles,text='管理分类',bg=COLORS['app_bg'],fg='#17213C',font=('Segoe UI Semibold',22)).pack(anchor='w');tk.Label(titles,text='创建分类并批量调整素材归属',bg=COLORS['app_bg'],fg=COLORS['muted'],font=('Segoe UI',10)).pack(anchor='w')
        self.stats=tk.Frame(top,bg=COLORS['app_bg']);self.stats.pack(side='left',padx=36)
        self.stat_labels=[]
        for icon,color in [('folder',COLORS['blue']),('batch','#22A579'),('photo','#6C4DE6')]:
            box=tk.Frame(self.stats,bg='white',highlightthickness=1,highlightbackground=COLORS['border']);box.pack(side='left',padx=5);SvgIcon(box,icon,color,'white',size=38,icon_size=20).pack(side='left',padx=(8,0),pady=5);v=tk.StringVar();self.stat_labels.append(v);tk.Label(box,textvariable=v,bg='white',fg='#17213C',font=('Segoe UI Semibold',10)).pack(side='left',padx=(2,12))
        self.save_btn=CanvasButton(top,'保存更改',icon='check',variant='primary',width=130,height=42,command=self.save);self.save_btn.pack(side='right');self.undo_btn=CanvasButton(top,'撤销上一步',icon='rescan',width=130,height=42,command=self.undo);self.undo_btn.pack(side='right',padx=10)
        body=tk.Frame(self,bg=COLORS['app_bg']);body.pack(fill='both',expand=True,padx=24,pady=(0,22));left=RoundedCard(body,padding=14,width=340);left.pack(side='left',fill='y',padx=(0,12));left.pack_propagate(False);right=RoundedCard(body,padding=14);right.pack(side='left',fill='both',expand=True)
        lh=tk.Frame(left.body,bg='white');lh.pack(fill='x');tk.Label(lh,text='分类文件夹',bg='white',fg='#17213C',font=('Segoe UI Semibold',15)).pack(side='left')
        search=tk.Frame(left.body,bg='white',highlightthickness=1,highlightbackground=COLORS['border']);search.pack(fill='x',pady=12);SvgIcon(search,'search',COLORS['muted'],'white',size=34,icon_size=18).pack(side='left');e=tk.Entry(search,textvariable=self.folder_query,relief='flat',bd=0,font=('Segoe UI',9));e.pack(fill='x',expand=True,ipady=8);e.bind('<KeyRelease>',lambda _e:self.category_canvas.redraw())
        CanvasButton(left.body,'新建分类',icon='add',variant='nav-active',height=40,command=self.create_folder).pack(fill='x',pady=(0,10));area=tk.Frame(left.body,bg='white');area.pack(fill='both',expand=True);self.category_canvas=CategoryCanvas(area,self);self.category_canvas.pack(side='left',fill='both',expand=True);scroll=ttk.Scrollbar(area,orient='vertical',command=self.category_canvas.yview);scroll.pack(side='right',fill='y');self.category_canvas.configure(yscrollcommand=scroll.set)
        la=tk.Frame(left.body,bg='white');la.pack(fill='x',pady=(10,0));CanvasButton(la,'重命名',icon='open',width=130,height=38,command=self.rename_folder).pack(side='left');CanvasButton(la,'删除分类',icon='delete',variant='danger',width=130,height=38,command=self.delete_folder).pack(side='right')
        rb=right.body;rh=tk.Frame(rb,bg='white');rh.pack(fill='x');self.right_title=tk.StringVar();tk.Label(rh,textvariable=self.right_title,bg='white',fg='#17213C',font=('Segoe UI Semibold',15)).pack(side='left')
        modes=tk.Frame(rh,bg='white');modes.pack(side='left',padx=20);self.mode_buttons={}
        for label,key in [('当前分类','current'),('未分类素材','unassigned'),('全部素材','all')]:
            b=CanvasButton(modes,label,width=100,height=36,command=lambda k=key:self.set_mode(k));b.pack(side='left',padx=2);self.mode_buttons[key]=b
        fs=tk.Frame(rh,bg='white',highlightthickness=1,highlightbackground=COLORS['border']);fs.pack(side='right');SvgIcon(fs,'search',COLORS['muted'],'white',size=32,icon_size=17).pack(side='left');fe=tk.Entry(fs,textvariable=self.file_query,relief='flat',bd=0,width=24,font=('Segoe UI',9));fe.pack(side='left',ipady=7);fe.bind('<KeyRelease>',lambda _e:self.refresh_files())
        self.actions=tk.Frame(rb,bg='#F7F9FC',highlightthickness=1,highlightbackground=COLORS['border']);self.actions.pack(fill='x',pady=(12,10));self.selected_text=tk.StringVar(value='已选择 0 项');tk.Label(self.actions,textvariable=self.selected_text,bg='#F7F9FC',fg='#17213C',font=('Segoe UI Semibold',9)).pack(side='left',padx=10)
        CanvasButton(self.actions,'全选',width=76,height=34,command=self.select_all).pack(side='left',padx=3);CanvasButton(self.actions,'取消选择',width=86,height=34,command=self.clear_selection).pack(side='left',padx=3);tk.Label(self.actions,text='移动到：',bg='#F7F9FC',fg=COLORS['muted']).pack(side='left',padx=(18,4));self.target_btn=CanvasButton(self.actions,'选择目标分类',icon='folder',width=150,height=34,command=self.show_targets);self.target_btn.pack(side='left');self.remove_btn=CanvasButton(self.actions,'移出当前分类',icon='rescan',width=130,height=34,command=self.remove_selected);self.remove_btn.pack(side='right',padx=4);self.move_btn=CanvasButton(self.actions,'移动所选素材',icon='export',variant='primary',width=140,height=34,command=self.move_selected);self.move_btn.pack(side='right',padx=4)
        table=tk.Frame(rb,bg='white');table.pack(fill='both',expand=True);cols=('file','kind','folder');self.files=ttk.Treeview(table,columns=cols,show='tree headings',selectmode='extended',style='ModernManager.Treeview');self.files.heading('#0',text='预览');self.files.heading('file',text='文件名');self.files.heading('kind',text='类型');self.files.heading('folder',text='当前分类');self.files.column('#0',width=104,stretch=False,anchor='center');self.files.column('file',width=430,anchor='w');self.files.column('kind',width=100,anchor='center');self.files.column('folder',width=150,anchor='center');vs=ttk.Scrollbar(table,orient='vertical',command=self.files.yview);self.files.configure(yscrollcommand=vs.set);self.files.pack(side='left',fill='both',expand=True);vs.pack(side='right',fill='y');self.files.bind('<<TreeviewSelect>>',lambda _e:self.selection_changed());self.files.bind('<ButtonPress-1>',self.drag_start,add='+');self.files.bind('<ButtonRelease-1>',self.drag_end,add='+');self.files.bind('<Motion>',self.file_motion,add='+');self.files.bind('<Leave>',self.hide_file_tooltip,add='+');self.file_tooltip=None;self.thumbnails=ManagerThumbnailColumn(self,self.files,self.app.rows)
        foot=tk.Frame(rb,bg='white');foot.pack(fill='x',pady=(8,0));SvgIcon(foot,'batch',COLORS['muted'],'white',size=30,icon_size=16).pack(side='left');tk.Label(foot,text='可将已选素材拖到左侧分类',bg='white',fg=COLORS['muted'],font=('Segoe UI',9)).pack(side='left');self.count_text=tk.StringVar();tk.Label(foot,textvariable=self.count_text,bg='white',fg=COLORS['muted']).pack(side='right')
    def snapshot(self):return (dict(self.staged),set(self.folder_set),self.current_folder)
    def push(self):self.undo_stack.append(self.snapshot());self.dirty=True
    def refresh_all(self):
        assigned=sum(bool(v) for v in self.staged.values());self.stat_labels[0].set(f'{len(self.folder_set)} 个自建分类');self.stat_labels[1].set(f'{assigned} 个已分类素材');self.stat_labels[2].set(f'{len(self.staged)-assigned} 个自动整理素材');self.undo_btn.configure(state='normal' if self.undo_stack else 'disabled');self.save_btn.configure(state='normal' if self.dirty else 'disabled');self.category_canvas.redraw();self.refresh_files();self.target_btn.configure(text=self.target.get() or '选择目标分类')
    def select_folder(self,name):self.current_folder=name;self.mode='current';self.target.set(next((x for x in sorted(self.folder_set) if x!=name),name));self.refresh_all()
    def set_mode(self,mode):self.mode=mode;self.refresh_files()
    def visible_indices(self):
        q=self.file_query.get().strip().lower();result=[]
        for i,row in enumerate(self.app.rows):
            folder=self.staged[i];ok=self.mode=='all' or(self.mode=='unassigned' and not folder)or(self.mode=='current' and folder==self.current_folder)
            if ok and(not q or q in row['p'].name.lower()):result.append(i)
        return result
    def duration(self,row):
        value=row.get('duration') or row.get('video_analysis',{}).get('duration') or 0
        try:value=int(float(value));return f' {value//60:02d}:{value%60:02d}' if value else ''
        except Exception:return ''
    def refresh_files(self):
        for k,b in self.mode_buttons.items():b.configure(variant='nav-active' if k==self.mode else 'secondary')
        self.files.delete(*self.files.get_children());ids=self.visible_indices()
        for i in ids:
            r=self.app.rows[i];kind=r.get('kind','');self.files.insert('','end',iid=str(i),values=(r['p'].name,kind+self.duration(r) if kind=='视频' else kind,self.staged[i] or '未分类'))
        self.right_title.set(f'{self.current_folder or "未分类"} 中的素材  {len(ids)} 项');self.count_text.set(f'共 {len(ids)} 项');self.after_idle(self.thumbnails.refresh);self.selection_changed()
    def selection_changed(self):
        n=len(self.files.selection());self.selected_text.set(f'已选择 {n} 项');state='normal' if n else 'disabled';self.move_btn.configure(state=state);self.remove_btn.configure(state=state if self.mode=='current' else 'disabled')
    def select_all(self):self.files.selection_set(self.files.get_children());self.selection_changed()
    def clear_selection(self):self.files.selection_remove(*self.files.selection());self.selection_changed()
    def ask_name(self,title,initial=''):
        raw=simpledialog.askstring(title,'分类名称：',initialvalue=initial,parent=self);name=valid_folder_name(raw)
        if not name or(name in self.folder_set and name!=initial):messagebox.showwarning('名称不可用','分类名称不能为空、不能重复，也不能包含 \\ / : * ? " < > |。',parent=self);return None
        return name
    def create_folder(self):
        name=self.ask_name('新建分类');
        if not name:return
        self.push();self.folder_set.add(name);self.current_folder=name;self.target.set(name);self.refresh_all()
    def rename_folder(self):
        old=self.current_folder
        if not old:return
        new=self.ask_name('重命名分类',old)
        if not new or new==old:return
        self.push();self.folder_set.discard(old);self.folder_set.add(new)
        for i,v in self.staged.items():
            if v==old:self.staged[i]=new
        self.current_folder=new;self.target.set(new);self.refresh_all()
    def delete_folder(self):
        name=self.current_folder
        if not name:return
        affected=[i for i,v in self.staged.items() if v==name]
        target=''
        if affected:
            choice=messagebox.askyesnocancel('删除非空分类',f'“{name}”中有 {len(affected)} 个素材。\n\n选择“是”：素材移至未分类。\n选择“否”：移至其他分类。',parent=self)
            if choice is None:return
            if not choice:
                choices=[x for x in sorted(self.folder_set) if x!=name]
                if not choices:return messagebox.showinfo('没有其他分类','请先创建其他分类，或选择移至未分类。',parent=self)
                target=simpledialog.askstring('移至其他分类','请输入目标分类：\n'+'、'.join(choices),parent=self) or ''
                if target not in choices:return messagebox.showwarning('目标无效','请输入现有的其他分类名称。',parent=self)
        self.push();self.folder_set.discard(name)
        for i in affected:self.staged[i]=target
        self.current_folder=next(iter(sorted(self.folder_set)),'');self.refresh_all()
    def show_targets(self):
        if self.target_popup and self.target_popup.winfo_exists():self.target_popup.destroy();self.target_popup=None;return
        p=tk.Toplevel(self);self.target_popup=p;p.overrideredirect(True);p.transient(self);p.configure(bg=COLORS['border']);body=tk.Frame(p,bg='white');body.pack(padx=1,pady=1)
        for name in sorted(self.folder_set):CanvasButton(body,name,width=180,height=34,command=lambda n=name:self.choose_target(n)).pack(fill='x',padx=5,pady=2)
        p.update_idletasks();x=self.target_btn.winfo_rootx();y=self.target_btn.winfo_rooty()+self.target_btn.winfo_height()+4;p.geometry(f'{p.winfo_reqwidth()}x{p.winfo_reqheight()}+{x}+{y}');p.lift()
    def choose_target(self,name):self.target.set(name);self.target_btn.configure(text=name);self.target_popup.destroy();self.target_popup=None
    def move_selected(self):
        ids=self.files.selection();target=self.target.get()
        if not ids or target not in self.folder_set:return
        self.push()
        for iid in ids:self.staged[int(iid)]=target
        self.current_folder=target;self.mode='current';self.refresh_all()
    def remove_selected(self):
        ids=self.files.selection()
        if not ids:return
        self.push()
        for iid in ids:self.staged[int(iid)]=''
        self.refresh_all()
    def undo(self):
        if not self.undo_stack:return
        self.staged,self.folder_set,self.current_folder=self.undo_stack.pop();self.dirty=self.staged!=self.original;self.refresh_all()
    def save(self):
        changed=set()
        for i,row in enumerate(self.app.rows):
            if row.get('custom_folder','')!=self.staged[i]:row['custom_folder']=self.staged[i];changed.add(str(row['p']))
        save_material_folders(self.app.rows,changed);self.original=dict(self.staged);self.undo_stack.clear();self.dirty=False;self.app.render();self.refresh_all();messagebox.showinfo('已保存',f'已保存 {len(changed)} 个素材的分类更改。',parent=self)
    def close(self):
        if self.dirty and not messagebox.askyesno('放弃未保存更改','当前有未保存的分类调整，确定放弃吗？',parent=self):return
        self.destroy()
    def file_motion(self,e):
        self.hide_file_tooltip()
        iid=self.files.identify_row(e.y);column=self.files.identify_column(e.x)
        if not iid or column!='#2':return
        name=self.app.rows[int(iid)]['p'].name
        if len(name)<34:return
        tip=tk.Toplevel(self);self.file_tooltip=tip;tip.overrideredirect(True);tip.attributes('-topmost',True);tip.geometry(f'+{e.x_root+12}+{e.y_root+12}');tk.Label(tip,text=name,bg=COLORS['text'],fg='white',padx=8,pady=4,font=('Segoe UI',8)).pack()
    def hide_file_tooltip(self,_e=None):
        if getattr(self,'file_tooltip',None):
            try:self.file_tooltip.destroy()
            except tk.TclError:pass
            self.file_tooltip=None
    def drag_start(self,e):self.dragging=bool(self.files.identify_row(e.y))
    def drag_end(self,e):
        if not self.dragging:return
        self.dragging=False;w=self.winfo_containing(e.x_root,e.y_root)
        if w is self.category_canvas:
            name=self.category_canvas.at(e.y_root-self.category_canvas.winfo_rooty())
            if name:
                ids=self.files.selection();self.push()
                for iid in ids:self.staged[int(iid)]=name
                self.current_folder=name;self.refresh_all()
