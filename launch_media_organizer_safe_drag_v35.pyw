import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from PIL import Image,ImageDraw,ImageTk

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scene-runtime'))
builtins.__file__=str(ROOT/'launch_scene_folder_final.pyw')
launcher=ROOT/'launch_media_organizer_safe_drag_v32.pyw'
source=launcher.read_text(encoding='utf-8').rsplit('SafeDragV32MediaOrganizerApp().mainloop()',1)[0]
scope={'__file__':str(launcher)}
exec(compile(source,str(launcher),'exec'),scope)
SafeDragV32MediaOrganizerApp=scope['SafeDragV32MediaOrganizerApp']

class SafeDragV35MediaOrganizerApp(SafeDragV32MediaOrganizerApp):
    COLORS={'bg':'#F3F1EB','surface':'#FFFFFF','text':'#18231C','muted':'#727971','green':'#68A982','green_dark':'#4E8866','green_soft':'#E4F3E9','border':'#E5E2DA','danger':'#A65757','danger_soft':'#F8E9E7','track':'#EEECE6'}
    def __init__(self):
        super().__init__();self._round_images={};self._skin_busy=False;self._create_rounded_styles();self._apply_rounded_skin();self.after_idle(self._apply_rounded_skin)
    def _rounded_image(self,name,size,radius,fill,outline=None,width=1):
        scale=3;w,h=size;im=Image.new('RGBA',(w*scale,h*scale),(0,0,0,0));d=ImageDraw.Draw(im);d.rounded_rectangle((1,1,w*scale-2,h*scale-2),radius=radius*scale,fill=fill,outline=outline,width=width*scale if outline else 1);im=im.resize((w,h),Image.Resampling.LANCZOS);photo=ImageTk.PhotoImage(im,master=self);self._round_images[name]=photo;return photo
    def _create_rounded_styles(self):
        c=self.COLORS;s=ttk.Style(self)
        try:s.theme_use('clam')
        except tk.TclError:pass
        self.configure(background=c['bg']);self.option_add('*Font',('Segoe UI',10))
        s.configure('TFrame',background=c['bg']);s.configure('TLabel',background=c['bg'],foreground=c['text']);s.configure('TLabelframe',background=c['bg'],bordercolor=c['border'],relief='flat');s.configure('TLabelframe.Label',background=c['bg'],foreground=c['text'],font=('Segoe UI Semibold',10))
        normal=self._rounded_image('button_normal',(140,38),19,c['surface'],c['border']);hover=self._rounded_image('button_hover',(140,38),19,c['green_soft'],c['green']);pressed=self._rounded_image('button_pressed',(140,38),19,'#D1EAD9',c['green'])
        primary=self._rounded_image('button_primary',(140,38),19,c['green']);primary_hover=self._rounded_image('button_primary_hover',(140,38),19,c['green_dark']);disabled=self._rounded_image('button_disabled',(140,38),19,'#C8D3CB')
        danger=self._rounded_image('button_danger',(140,38),19,c['danger_soft']);danger_hover=self._rounded_image('button_danger_hover',(140,38),19,'#F0D2CF')
        off=self._rounded_image('pill_off',(190,36),18,c['surface'],c['border']);off_hover=self._rounded_image('pill_off_hover',(190,36),18,c['green_soft'],c['green']);on=self._rounded_image('pill_on',(190,36),18,c['green']);on_hover=self._rounded_image('pill_on_hover',(190,36),18,c['green_dark'])
        entry=self._rounded_image('entry',(220,38),19,c['surface'],c['border']);entry_focus=self._rounded_image('entry_focus',(220,38),19,c['surface'],c['green'],2)
        track=self._rounded_image('progress_track',(260,18),9,c['track'],c['border']);bar=self._rounded_image('progress_bar',(120,18),9,c['green'])
        try:
            s.element_create('RoundButton.background','image',normal,('pressed',pressed),('active',hover),border=19,sticky='nsew')
            s.element_create('PrimaryButton.background','image',primary,('disabled',disabled),('pressed',primary_hover),('active',primary_hover),border=19,sticky='nsew')
            s.element_create('DangerButton.background','image',danger,('pressed',danger_hover),('active',danger_hover),border=19,sticky='nsew')
            s.element_create('PillCheck.background','image',off,('selected active',on_hover),('selected',on),('active',off_hover),border=18,sticky='nsew')
            s.element_create('RoundEntry.field','image',entry,('focus',entry_focus),border=19,sticky='nsew')
            s.element_create('RoundProgress.trough','image',track,border=9,sticky='nsew')
            s.element_create('RoundProgress.pbar','image',bar,border=9,sticky='nsew')
        except tk.TclError:pass
        button_layout=[('RoundButton.background',{'sticky':'nsew','children':[('Button.padding',{'sticky':'nsew','children':[('Button.label',{'sticky':'nsew'})]})]})]
        primary_layout=[('PrimaryButton.background',{'sticky':'nsew','children':[('Button.padding',{'sticky':'nsew','children':[('Button.label',{'sticky':'nsew'})]})]})]
        danger_layout=[('DangerButton.background',{'sticky':'nsew','children':[('Button.padding',{'sticky':'nsew','children':[('Button.label',{'sticky':'nsew'})]})]})]
        pill_layout=[('PillCheck.background',{'sticky':'nsew','children':[('Checkbutton.padding',{'sticky':'nsew','children':[('Checkbutton.label',{'sticky':'nsew'})]})]})]
        entry_layout=[('RoundEntry.field',{'sticky':'nsew','children':[('Entry.padding',{'sticky':'nsew','children':[('Entry.textarea',{'sticky':'nsew'})]})]})]
        progress_layout=[('RoundProgress.trough',{'sticky':'nsew','children':[('RoundProgress.pbar',{'side':'left','sticky':'ns'})]})]
        s.layout('Rounded.TButton',button_layout);s.layout('Primary.Rounded.TButton',primary_layout);s.layout('Danger.Rounded.TButton',danger_layout);s.layout('Pill.TCheckbutton',pill_layout);s.layout('Rounded.TEntry',entry_layout);s.layout('Rounded.Horizontal.TProgressbar',progress_layout)
        s.configure('Rounded.TButton',foreground=c['text'],padding=(16,9),font=('Segoe UI Semibold',9),anchor='center');s.configure('Primary.Rounded.TButton',foreground='white',padding=(18,9),font=('Segoe UI Semibold',9),anchor='center');s.configure('Danger.Rounded.TButton',foreground=c['danger'],padding=(16,9),font=('Segoe UI Semibold',9),anchor='center')
        s.configure('Pill.TCheckbutton',foreground=c['text'],padding=(15,8),font=('Segoe UI Semibold',9),anchor='center');s.map('Pill.TCheckbutton',foreground=[('selected','white'),('!selected',c['text'])])
        s.configure('Rounded.TEntry',foreground=c['text'],padding=(12,8));s.configure('Rounded.Horizontal.TProgressbar',thickness=18)
        s.configure('TNotebook',background=c['bg'],borderwidth=0);s.configure('TNotebook.Tab',background=c['surface'],foreground=c['muted'],padding=(18,9),borderwidth=0);s.map('TNotebook.Tab',background=[('selected',c['green_soft'])],foreground=[('selected',c['green_dark'])])
        s.configure('Treeview',background=c['surface'],fieldbackground=c['surface'],foreground=c['text'],rowheight=54,borderwidth=0);s.map('Treeview',background=[('selected',c['green_soft'])],foreground=[('selected',c['text'])]);s.configure('Treeview.Heading',background='#F8F7F3',foreground=c['muted'],relief='flat',padding=(8,8),font=('Segoe UI Semibold',9))
    def _apply_rounded_skin(self):
        if self._skin_busy:return
        self._skin_busy=True
        try:
            for w in self._descendants(self):
                kind=w.winfo_class()
                try:text=str(w.cget('text'))
                except (tk.TclError,AttributeError):text=''
                try:
                    if kind=='TButton':w.configure(style='Primary.Rounded.TButton' if text in {'扫描并预览','扫描并预览 →','执行整理','✨ AI识别'} else 'Danger.Rounded.TButton' if text=='从整理中删除' else 'Rounded.TButton')
                    elif kind=='TCheckbutton':w.configure(style='Pill.TCheckbutton')
                    elif kind=='TEntry':w.configure(style='Rounded.TEntry')
                    elif kind=='TProgressbar':w.configure(style='Rounded.Horizontal.TProgressbar')
                    elif kind=='Listbox':w.configure(background=self.COLORS['surface'],foreground=self.COLORS['text'],selectbackground=self.COLORS['green_soft'],selectforeground=self.COLORS['text'],relief='flat',borderwidth=0,highlightthickness=1,highlightbackground=self.COLORS['border'],highlightcolor=self.COLORS['green'])
                except tk.TclError:pass
        finally:self._skin_busy=False
    def render(self):
        super().render();self.after_idle(self._apply_rounded_skin)

SafeDragV35MediaOrganizerApp().mainloop()
