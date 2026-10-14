import re
import tkinter as tk
from v3_ui_components import COLORS, rounded_rectangle

# One 24x24 viewBox, 2px rounded strokes. Every glyph is defined as SVG path data.
SVG_PATHS={
'add':'M12 5 L12 19 M5 12 L19 12','check':'M4 12 L9 17 L20 6','organize':'M5 4 L19 4 L19 8 L5 8 Z M5 10 L19 10 L19 14 L5 14 Z M5 16 L19 16 L19 20 L5 20 Z',
'chevron-left':'M15 5 L8 12 L15 19','chevron-right':'M9 5 L16 12 L9 19','close':'M6 6 L18 18 M18 6 L6 18',
'folder':'M3 6 L9 6 L11 9 L21 9 L21 19 L3 19 Z','folder-upload':'M3 7 L9 7 L11 10 L21 10 L21 20 L3 20 Z M12 17 L12 11 M9 14 L12 11 L15 14','photo':'M3 4 L21 4 L21 20 L3 20 Z M6 16 L10 11 L13 14 L16 10 L20 16 M16 8 L18 8',
'video':'M3 6 L15 6 L15 18 L3 18 Z M15 10 L21 7 L21 17 L15 14 Z','warning':'M12 3 L22 20 L2 20 Z M12 8 L12 14 M12 17 L12 18',
'search':'M10 3 L14 4 L17 7 L18 11 L17 15 L14 18 L10 19 L6 18 L3 15 L2 11 L3 7 L6 4 Z M16 17 L22 23',
'scan':'M12 5 L12 2 M12 22 L12 19 M5 12 L2 12 M22 12 L19 12 M12 6 L16 8 L18 12 L16 16 L12 18 L8 16 L6 12 L8 8 Z',
'filter':'M3 5 L21 5 L14 13 L14 20 L10 18 L10 13 Z','batch':'M4 7 L7 10 L11 5 M13 7 L21 7 M4 15 L7 18 L11 13 M13 15 L21 15',
'export':'M12 3 L12 15 M7 8 L12 3 L17 8 M4 14 L4 21 L20 21 L20 14','play':'M8 5 L19 12 L8 19 Z','stop':'M6 6 L18 6 L18 18 L6 18 Z','rescan':'M20 7 L20 3 L16 3 M20 4 L17 7 M17 7 L14 5 L10 4 L6 6 L4 10 L4 14 L6 18 L10 20 L14 19 L18 16','pause':'M8 5 L8 19 M16 5 L16 19',
'settings':'M12 3 L15 5 L19 5 L19 9 L21 12 L19 15 L19 19 L15 19 L12 21 L9 19 L5 19 L5 15 L3 12 L5 9 L5 5 L9 5 Z M9 12 L10 9 L14 9 L15 12 L14 15 L10 15 Z',
'delete':'M5 7 L19 7 M9 7 L9 4 L15 4 L15 7 M7 7 L8 21 L16 21 L17 7','open':'M4 4 L13 4 L13 7 L4 7 L4 20 L17 20 L17 12 M11 13 L21 3 M15 3 L21 3 L21 9',
'layers':'M12 3 L21 8 L12 13 L3 8 Z M3 12 L12 17 L21 12 M3 16 L12 21 L21 16','help':'M9 9 L10 6 L14 6 L16 8 L16 10 L12 13 L12 15 M12 19 L12 20','duplicate':'M8 8 L20 8 L20 20 L8 20 Z M4 16 L4 4 L16 4','more':'M5 12 L6 12 M12 12 L13 12 M19 12 L20 12','star':'M12 3 L15 9 L22 10 L17 15 L18 22 L12 19 L6 22 L7 15 L2 10 L9 9 Z','star-fill':'M12 3 L15 9 L22 10 L17 15 L18 22 L12 19 L6 22 L7 15 L2 10 L9 9 Z','arrow-left':'M15 5 L8 12 L15 19','arrow-right':'M9 5 L16 12 L9 19','columns':'M3 5 L21 5 L21 19 L3 19 Z M9 5 L9 19 M15 5 L15 19','smart':'M12 2 L14 9 L21 12 L14 15 L12 22 L10 15 L3 12 L10 9 Z M19 3 L20 5 L22 6 L20 7 L19 9 L18 7 L16 6 L18 5 Z'
}

def _segments(path):
 tokens=re.findall(r'[MLHVZ]|-?\d+(?:\.\d+)?',path);i=0;x=y=0;start=(0,0);lines=[]
 while i<len(tokens):
  cmd=tokens[i];i+=1
  if cmd=='M': x=float(tokens[i]);y=float(tokens[i+1]);i+=2;start=(x,y)
  elif cmd=='L': nx=float(tokens[i]);ny=float(tokens[i+1]);i+=2;lines.append((x,y,nx,ny));x,y=nx,ny
  elif cmd=='H': nx=float(tokens[i]);i+=1;lines.append((x,y,nx,y));x=nx
  elif cmd=='V': ny=float(tokens[i]);i+=1;lines.append((x,y,x,ny));y=ny
  elif cmd=='Z': lines.append((x,y,start[0],start[1]));x,y=start
 return lines

def draw_svg_icon(canvas,kind,cx,cy,size,color,width=2):
 scale=size/24;ox=cx-size/2;oy=cy-size/2
 for x1,y1,x2,y2 in _segments(SVG_PATHS.get(kind,SVG_PATHS['more'])):
  canvas.create_line(ox+x1*scale,oy+y1*scale,ox+x2*scale,oy+y2*scale,fill=color,width=width,capstyle='round',joinstyle='round')

class SvgIcon(tk.Canvas):
 def __init__(self,master,kind,color=None,bg='#EEF2FF',size=46,icon_size=24,**kwargs):
  self.kind=kind;self.color=color or COLORS['blue'];self.tile_bg=bg;self.size=size;self.icon_size=icon_size
  super().__init__(master,width=size,height=size,background=master.cget('background'),highlightthickness=0,borderwidth=0,**kwargs);self.bind('<Configure>',self._draw);self._draw()
 def _draw(self,_event=None):
  self.delete('all');rounded_rectangle(self,1,1,self.size-1,self.size-1,10,fill=self.tile_bg,outline='');draw_svg_icon(self,self.kind,self.size/2,self.size/2,self.icon_size,self.color,2)
