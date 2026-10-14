import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_sidebar_layout.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SidebarLayoutMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SidebarLayoutMediaOrganizerApp = scope['SidebarLayoutMediaOrganizerApp']


class CollapsibleSidebarMediaOrganizerApp(SidebarLayoutMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.sidebar_visible = tk.BooleanVar(value=True)
        self.sidebar_grip.configure(width=24)
        self.sidebar_toggle = ttk.Button(self.sidebar_grip, text='◀', width=2, command=self.toggle_sidebar, cursor='hand2')
        self.sidebar_toggle.place(relx=0.5, rely=0.5, anchor='center')
        self.sidebar_toggle.lift()

    def toggle_sidebar(self):
        if self.sidebar_visible.get():
            self.sidebar.pack_forget()
            self.sidebar_visible.set(False)
            self.sidebar_toggle.configure(text='▶')
            self.status.set('文件夹列表已隐藏；点击边界箭头可重新打开')
        else:
            self.sidebar.pack(side='left', fill='y', padx=(8, 3), pady=(0, 4), before=self.sidebar_grip)
            self.sidebar_visible.set(True)
            self.sidebar_toggle.configure(text='◀')
            self.status.set('文件夹列表已打开；可拖动边界调整宽度')

    def start_sidebar_resize(self, event):
        if not self.sidebar_visible.get(): self.toggle_sidebar()
        super().start_sidebar_resize(event)


CollapsibleSidebarMediaOrganizerApp().mainloop()
