import tkinter as tk
import tkinter.font as tkfont
COLORS={'app_bg':'#E9ECF2','card':'#FFFFFF','sidebar':'#26365F','sidebar_alt':'#3E4C78','text':'#1F2430','muted':'#6F7685','coral':'#F2645A','coral_hover':'#E9574E','blue':'#4263EB','success':'#62A98B','warning':'#E85B55','border':'#DCE2EC','soft':'#F4F6FA','soft_blue':'#EEF2FF','disabled':'#C7CCD6'}
def rounded_rectangle(canvas,x1,y1,x2,y2,radius=16,**kwargs):
 radius=max(1,min(radius,(x2-x1)/2,(y2-y1)/2));points=[x1+radius,y1,x2-radius,y1,x2,y1,x2,y1+radius,x2,y2-radius,x2,y2,x2-radius,y2,x1+radius,y2,x1,y2,x1,y2-radius,x1,y1+radius,x1,y1];return canvas.create_polygon(points,smooth=True,splinesteps=24,**kwargs)
class RoundedCard(tk.Canvas):
 def __init__(self,master,radius=16,fill=None,outline=None,padding=18,**kwargs):
  self.fill=fill or COLORS['card'];self.outline=outline or COLORS['border'];self.radius=radius;self.padding=padding
  try: master_bg=master.cget('background')
  except tk.TclError: master_bg=COLORS['app_bg']
  kwargs.setdefault('background',master_bg);kwargs.setdefault('highlightthickness',0);kwargs.setdefault('borderwidth',0);super().__init__(master,**kwargs);self.body=tk.Frame(self,background=self.fill);self._window=self.create_window(padding,padding,anchor='nw',window=self.body);self.bind('<Configure>',self._resize)
 def _resize(self,event=None):
  width=max(2,self.winfo_width());height=max(2,self.winfo_height());self.delete('card-shape');rounded_rectangle(self,1,1,width-1,height-1,self.radius,fill=self.fill,outline=self.outline,width=1,tags='card-shape');self.tag_lower('card-shape');self.itemconfigure(self._window,width=max(1,width-self.padding*2),height=max(1,height-self.padding*2))
class CanvasButton(tk.Canvas):
 def __init__(self,master,text,command=None,variant='secondary',width=150,height=42,radius=8,icon='',font=None,**kwargs):
  self._text=text;self._icon=icon;self._command=command;self._variant=variant;self._state='normal';self._hover=False;self._radius=radius;self._font=font or ('Segoe UI Semibold',10);super().__init__(master,width=width,height=height,highlightthickness=0,borderwidth=0,background=master.cget('background'),cursor='hand2',**kwargs);self.bind('<Enter>',lambda _e:self._set_hover(True));self.bind('<Leave>',lambda _e:self._set_hover(False));self.bind('<ButtonRelease-1>',self._invoke);self.bind('<Configure>',lambda _e:self._draw());self._draw()
 def _palette(self):
  if self._state=='disabled':return COLORS['disabled'],COLORS['disabled'],'#FFFFFF'
  if self._variant=='primary':return (COLORS['coral_hover'] if self._hover else COLORS['coral']),COLORS['coral_hover'],'#FFFFFF'
  if self._variant=='nav':return (COLORS['sidebar_alt'] if self._hover else COLORS['sidebar']),COLORS['sidebar'],'#FFFFFF'
  if self._variant=='nav-active':return '#405793','#405793','#FFFFFF'
  if self._variant=='danger':return ('#FFF2F1' if not self._hover else '#FDE5E3'),'#F5C4C0',COLORS['warning']
  return ('#FFFFFF' if not self._hover else COLORS['soft']),COLORS['border'],COLORS['text']
 def _draw(self):
  self.delete('all');fill,outline,foreground=self._palette();width=max(2,self.winfo_width());height=max(2,self.winfo_height());rounded_rectangle(self,1,1,width-1,height-1,self._radius,fill=fill,outline=outline,width=1);label=self._text
  if self._icon:
   try:
    from svg_icon_system import draw_svg_icon,SVG_PATHS
    if self._icon in SVG_PATHS:
     if label:
      text_width=tkfont.Font(font=self._font).measure(label);icon_size=18;gap=8;group_width=icon_size+gap+text_width;group_left=(width-group_width)/2;ix=group_left+icon_size/2;tx=group_left+icon_size+gap+text_width/2
      draw_svg_icon(self,self._icon,ix,height/2,icon_size,foreground,2);self.create_text(tx,height/2,text=label,fill=foreground,font=self._font);return
     draw_svg_icon(self,self._icon,width/2,height/2,18,foreground,2)
    else:label=self._text
   except Exception:pass
  if label:self.create_text(width/2,height/2,text=label,fill=foreground,font=self._font)
 def _set_hover(self,value):self._hover=value and self._state!='disabled';super().configure(cursor='hand2' if self._state!='disabled' else 'arrow');self._draw()
 def _invoke(self,_event=None):
  if self._state!='disabled' and self._command:self._command()
 def invoke(self):self._invoke()
 def configure(self,cnf=None,**kwargs):
  if cnf:kwargs.update(cnf)
  redraw=False
  for key in ('text','state','command','variant','icon'):
   if key in kwargs:setattr(self,f'_{key}',kwargs.pop(key));redraw=True
  result=super().configure(**kwargs)
  if redraw:self._draw()
  return result
 config=configure
 def cget(self,key):
  if key in {'text','state','command','variant','icon'}:return getattr(self,f'_{key}')
  return super().cget(key)
 def state(self,statespec=None):
  if statespec is None:return ('disabled',) if self._state=='disabled' else ()
  for state in statespec:
   if state=='disabled':self._state='disabled'
   elif state=='!disabled':self._state='normal'
  self._draw();return self.state()
class ToggleSwitch(tk.Canvas):
 def __init__(self,master,variable,command=None,width=48,height=26,**kwargs):
  self.variable=variable;self.command=command;self._track_width=width;self._track_height=height;super().__init__(master,width=width,height=height,background=master.cget('background'),highlightthickness=0,borderwidth=0,cursor='hand2',**kwargs);self.bind('<ButtonRelease-1>',self._toggle);self._trace=self.variable.trace_add('write',self._variable_changed);self._draw()
 def _variable_changed(self,*_args):
  try:
   if self.winfo_exists():self._draw()
  except tk.TclError:pass
 def _toggle(self,_event=None):self.variable.set(not bool(self.variable.get()));self.command() if self.command else None
 def _draw(self):
  self.delete('all');selected=bool(self.variable.get());fill=COLORS['blue'] if selected else '#BCC4D3';rounded_rectangle(self,1,1,self._track_width-1,self._track_height-1,self._track_height/2,fill=fill,outline=fill);radius=(self._track_height-6)/2;cx=self._track_width-radius-3 if selected else radius+3;self.create_oval(cx-radius,3,cx+radius,self._track_height-3,fill='#FFFFFF',outline='#FFFFFF')
class SegmentedControl(tk.Frame):
 def __init__(self,master,variable,options,command=None,**kwargs):
  super().__init__(master,background=master.cget('background'),**kwargs);self.variable=variable;self.command=command;self.buttons=[]
  for label,value in options:
   button=CanvasButton(self,label,command=lambda v=value:self.select(v),width=145,height=40,radius=8);button.pack(side='left',padx=(0,8));self.buttons.append((button,value))
  variable.trace_add('write',lambda *_:self._refresh());self._refresh()
 def select(self,value):self.variable.set(value);self.command() if self.command else None
 def _refresh(self):
  current=self.variable.get()
  for button,value in self.buttons:button._variant='nav-active' if current==value else 'secondary';button._draw()
class Tooltip:
 def __init__(self,widget,text_getter):self.widget=widget;self.text_getter=text_getter;self.popup=None;widget.bind('<Enter>',self.show,add='+');widget.bind('<Leave>',self.hide,add='+')
 def show(self,_event=None):
  text=self.text_getter() if callable(self.text_getter) else self.text_getter
  if not text:return
  self.popup=tk.Toplevel(self.widget);self.popup.overrideredirect(True);self.popup.attributes('-topmost',True);self.popup.geometry(f'+{self.widget.winfo_rootx()+12}+{self.widget.winfo_rooty()+self.widget.winfo_height()+6}');tk.Label(self.popup,text=text,background=COLORS['text'],foreground='white',padx=9,pady=5,font=('Segoe UI',9)).pack()
 def hide(self,_event=None):
  if self.popup is not None:self.popup.destroy();self.popup=None
class PathList(tk.Frame):
 def __init__(self,master,items_getter,remove_command,empty_text='暂无目录',**kwargs):super().__init__(master,background=master.cget('background'),**kwargs);self.items_getter=items_getter;self.remove_command=remove_command;self.empty_text=empty_text
 def refresh(self):
  for child in self.winfo_children():child.destroy()
  items=list(self.items_getter())
  if not items:tk.Label(self,text=self.empty_text,background=self.cget('background'),foreground=COLORS['muted'],font=('Segoe UI',9)).pack(anchor='w',pady=8);return
  for index,path in enumerate(items):
   row=tk.Frame(self,background=COLORS['soft'],height=42);row.pack(fill='x',pady=3);row.pack_propagate(False)
   from svg_icon_system import SvgIcon
   SvgIcon(row,'folder',COLORS['sidebar'],COLORS['soft'],size=30,icon_size=18).pack(side='left',padx=(8,4));label=tk.Label(row,text=str(path),background=COLORS['soft'],foreground=COLORS['text'],anchor='w',font=('Segoe UI',9));label.pack(side='left',fill='x',expand=True);remove=SvgIcon(row,'delete',COLORS['muted'],COLORS['soft'],size=36,icon_size=16,cursor='hand2');remove.pack(side='right',padx=4);remove.bind('<ButtonRelease-1>',lambda _e,i=index:self.remove_command(i));Tooltip(label,str(path))


class LineIcon(tk.Canvas):
 def __init__(self,master,kind,color=None,bg='#EEF2FF',size=46,**kwargs):
  self.kind=kind;self.color=color or COLORS['blue'];self.tile_bg=bg;self.size=size
  super().__init__(master,width=size,height=size,background=master.cget('background'),highlightthickness=0,borderwidth=0,**kwargs);self.bind('<Configure>',self._draw);self._draw()
 def _draw(self,_event=None):
  self.delete('all');s=self.size;c=self.color
  rounded_rectangle(self,1,1,s-1,s-1,10,fill=self.tile_bg,outline='')
  x=s/2;y=s/2;w=2
  if self.kind=='scan':
   self.create_oval(x-7,y-7,x+7,y+7,outline=c,width=w);self.create_line(x,y-14,x,y-8,fill=c,width=w);self.create_line(x,y+8,x,y+14,fill=c,width=w);self.create_line(x-14,y,x-8,y,fill=c,width=w);self.create_line(x+8,y,x+14,y,fill=c,width=w)
  elif self.kind=='folder':
   self.create_line(x-14,y-8,x-5,y-8,x-2,y-4,x+14,y-4,x+14,y+11,x-14,y+11,x-14,y-8,fill=c,width=w,joinstyle='round')
  elif self.kind=='photo':
   self.create_rectangle(x-13,y-11,x+13,y+11,outline=c,width=w);self.create_oval(x+4,y-7,x+8,y-3,outline=c,width=w);self.create_line(x-10,y+7,x-3,y,x+2,y+5,x+7,y,x+11,y+6,fill=c,width=w)
  elif self.kind=='video':
   self.create_rectangle(x-13,y-9,x+5,y+9,outline=c,width=w);self.create_polygon(x+6,y-5,x+14,y-10,x+14,y+10,x+6,y+5,outline=c,fill='',width=w)
  elif self.kind=='warning':
   self.create_polygon(x,y-14,x+14,y+12,x-14,y+12,outline=c,fill='',width=w);self.create_line(x,y-6,x,y+3,fill=c,width=w);self.create_oval(x-1,y+7,x+1,y+9,fill=c,outline=c)
  elif self.kind=='search':
   self.create_oval(x-8,y-8,x+4,y+4,outline=c,width=w);self.create_line(x+3,y+3,x+10,y+10,fill=c,width=w)
  elif self.kind=='settings':
   self.create_oval(x-7,y-7,x+7,y+7,outline=c,width=w);self.create_oval(x-2,y-2,x+2,y+2,outline=c,width=w)
