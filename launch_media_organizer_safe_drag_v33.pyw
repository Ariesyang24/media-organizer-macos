import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scene-runtime'))
builtins.__file__=str(ROOT/'launch_scene_folder_final.pyw')
launcher=ROOT/'launch_media_organizer_safe_drag_v32.pyw'
source=launcher.read_text(encoding='utf-8').rsplit('SafeDragV32MediaOrganizerApp().mainloop()',1)[0]
scope={'__file__':str(launcher)}
exec(compile(source,str(launcher),'exec'),scope)
SafeDragV32MediaOrganizerApp=scope['SafeDragV32MediaOrganizerApp']

class SafeDragV33MediaOrganizerApp(SafeDragV32MediaOrganizerApp):
    COLORS={'background':'#F3F1EB','surface':'#FFFEFB','surface_alt':'#F8F6F0','text':'#17221C','muted':'#6E776F','accent':'#6EAD86','accent_dark':'#47795B','accent_soft':'#DDF2E4','accent_pale':'#EDF7F0','border':'#DDDCD5','danger':'#A55252','danger_soft':'#F8E7E5'}
    def __init__(self):
        super().__init__();self._theme_busy=False;self._configure_dashboard_theme();self._apply_dashboard_styles();self.after_idle(self._apply_dashboard_styles)
    def _configure_dashboard_theme(self):
        c=self.COLORS;self.configure(background=c['background']);self.option_add('*Font',('Segoe UI',10));self.option_add('*Listbox.Font',('Segoe UI',10));style=ttk.Style(self)
        try:style.theme_use('clam')
        except tk.TclError:pass
        style.configure('.',background=c['background'],foreground=c['text'],font=('Segoe UI',10),bordercolor=c['border'])
        style.configure('TFrame',background=c['background']);style.configure('Header.TFrame',background=c['surface'],padding=(18,13));style.configure('Card.TFrame',background=c['surface'])
        style.configure('TLabel',background=c['background'],foreground=c['text']);style.configure('Card.TLabel',background=c['surface'],foreground=c['text'])
        style.configure('Hero.TLabel',background=c['surface'],foreground=c['text'],font=('Segoe UI Semibold',22));style.configure('SectionTitle.TLabel',foreground=c['text'],font=('Segoe UI Semibold',16))
        style.configure('Muted.TLabel',foreground=c['muted'],font=('Segoe UI',9));style.configure('CardMuted.TLabel',background=c['surface'],foreground=c['muted'],font=('Segoe UI',9));style.configure('Count.TLabel',foreground=c['accent_dark'],font=('Segoe UI Semibold',10))
        style.configure('TButton',background=c['surface'],foreground=c['text'],borderwidth=1,relief='flat',padding=(13,8),font=('Segoe UI Semibold',9));style.map('TButton',background=[('pressed',c['accent_soft']),('active',c['accent_pale'])],bordercolor=[('focus',c['accent']),('active',c['accent'])])
        style.configure('Accent.TButton',background=c['accent'],foreground='#FFFFFF',borderwidth=0,padding=(17,9),font=('Segoe UI Semibold',10));style.map('Accent.TButton',background=[('pressed',c['accent_dark']),('active','#5F9F78'),('disabled','#B9CBBF')],foreground=[('disabled','#F6F6F3')])
        style.configure('Soft.TButton',background=c['accent_soft'],foreground=c['accent_dark'],borderwidth=0,padding=(14,9));style.map('Soft.TButton',background=[('pressed','#C8E7D3'),('active','#D2EDDB')])
        style.configure('Stat.TButton',background=c['surface'],foreground=c['text'],borderwidth=1,padding=(18,14),font=('Segoe UI Semibold',10));style.map('Stat.TButton',background=[('pressed',c['accent_soft']),('active',c['accent_pale'])],bordercolor=[('focus',c['accent']),('active',c['accent'])])
        style.configure('Danger.TButton',background=c['danger_soft'],foreground=c['danger'],borderwidth=0,padding=(13,8));style.map('Danger.TButton',background=[('pressed','#EFCFCD'),('active','#F3DAD8')])
        style.configure('Icon.TButton',background=c['accent_soft'],foreground=c['accent_dark'],borderwidth=0,padding=(9,6),font=('Segoe UI Semibold',12))
        style.configure('TCheckbutton',background=c['background'],foreground=c['text'],padding=(3,4));style.map('TCheckbutton',background=[('active',c['background'])],indicatorcolor=[('selected',c['accent']),('!selected',c['surface'])])
        style.configure('Card.TCheckbutton',background=c['surface'],foreground=c['text']);style.map('Card.TCheckbutton',background=[('active',c['surface'])],indicatorcolor=[('selected',c['accent']),('!selected',c['surface'])])
        style.configure('TLabelframe',background=c['surface'],borderwidth=1,relief='solid',bordercolor=c['border']);style.configure('TLabelframe.Label',background=c['surface'],foreground=c['text'],font=('Segoe UI Semibold',10),padding=(4,2))
        style.configure('TNotebook',background=c['background'],borderwidth=0,tabmargins=(8,6,8,0));style.configure('TNotebook.Tab',background=c['surface_alt'],foreground=c['muted'],borderwidth=0,padding=(18,9),font=('Segoe UI Semibold',9));style.map('TNotebook.Tab',background=[('selected',c['accent_soft']),('active',c['accent_pale'])],foreground=[('selected',c['accent_dark']),('active',c['text'])])
        style.configure('Treeview',background=c['surface'],fieldbackground=c['surface'],foreground=c['text'],borderwidth=0,relief='flat',rowheight=62,font=('Segoe UI',10));style.map('Treeview',background=[('selected',c['accent_soft'])],foreground=[('selected',c['text'])])
        style.configure('Treeview.Heading',background=c['surface_alt'],foreground=c['muted'],relief='flat',borderwidth=0,padding=(9,9),font=('Segoe UI Semibold',9));style.map('Treeview.Heading',background=[('active',c['accent_pale'])])
        style.configure('TEntry',fieldbackground=c['surface'],foreground=c['text'],bordercolor=c['border'],lightcolor=c['border'],darkcolor=c['border'],padding=(8,7));style.map('TEntry',bordercolor=[('focus',c['accent'])],lightcolor=[('focus',c['accent'])],darkcolor=[('focus',c['accent'])])
        style.configure('TCombobox',fieldbackground=c['surface'],background=c['surface'],foreground=c['text'],arrowcolor=c['accent_dark'],padding=(8,6));style.map('TCombobox',fieldbackground=[('readonly',c['surface'])],bordercolor=[('focus',c['accent'])])
        style.configure('Horizontal.TProgressbar',background=c['accent'],troughcolor=c['surface_alt'],borderwidth=0,thickness=12);style.configure('TSeparator',background=c['border'])
        for name in ('Vertical.TScrollbar','Horizontal.TScrollbar'):style.configure(name,background=c['surface_alt'],troughcolor=c['surface'],borderwidth=0,arrowcolor=c['muted'])
    def _inside_card(self,widget):
        parent=widget.master
        while parent is not None and parent is not self:
            if parent.winfo_class()=='TLabelframe':return True
            parent=getattr(parent,'master',None)
        return False
    def _apply_dashboard_styles(self):
        if self._theme_busy:return
        self._theme_busy=True;c=self.COLORS
        try:
            top=self.winfo_children()
            if top and top[0].winfo_class()=='TFrame':top[0].configure(style='Header.TFrame',padding=(18,13))
            for widget in self._descendants(self):
                kind=widget.winfo_class()
                try:text=str(widget.cget('text'))
                except (tk.TclError,AttributeError):text=''
                card=self._inside_card(widget)
                try:
                    if kind=='TFrame' and card:widget.configure(style='Card.TFrame')
                    elif kind=='TLabel':
                        if text=='Media Organizer':widget.configure(style='Hero.TLabel')
                        elif text=='准备素材':widget.configure(style='SectionTitle.TLabel')
                        elif any(part in text for part in ('按日期地点','按需展开','照片直接识别','默认只复制','也可以多选','统一在左侧完成')):widget.configure(style='CardMuted.TLabel' if card else 'Muted.TLabel')
                        elif text.isdigit():widget.configure(style='Count.TLabel')
                        elif card:widget.configure(style='Card.TLabel')
                    elif kind=='TCheckbutton' and card:widget.configure(style='Card.TCheckbutton')
                    elif kind=='TButton':
                        if text in {'扫描并预览','扫描并预览 →','执行整理','✨ AI识别'}:widget.configure(style='Accent.TButton')
                        elif text.startswith('📁'):widget.configure(style='Stat.TButton')
                        elif text=='从整理中删除':widget.configure(style='Danger.TButton')
                        elif text in {'＋','+ 新建文件夹','+ 新建文件夹并放入选中素材'}:widget.configure(style='Icon.TButton' if text=='＋' else 'Soft.TButton')
                    elif kind=='Listbox':widget.configure(background=c['surface'],foreground=c['text'],selectbackground=c['accent_soft'],selectforeground=c['text'],borderwidth=0,relief='flat',highlightthickness=1,highlightbackground=c['border'],highlightcolor=c['accent'],activestyle='none')
                    elif kind=='Canvas':widget.configure(background=c['surface'],highlightthickness=0)
                except tk.TclError:pass
        finally:self._theme_busy=False
    def render(self):
        super().render();self.after_idle(self._apply_dashboard_styles)

SafeDragV33MediaOrganizerApp().mainloop()
