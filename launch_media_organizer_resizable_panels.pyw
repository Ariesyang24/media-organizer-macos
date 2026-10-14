import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_mac_folders.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('MacFolderBehaviorMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
MacFolderBehaviorMediaOrganizerApp = scope['MacFolderBehaviorMediaOrganizerApp']


class ResizablePanelsMediaOrganizerApp(MacFolderBehaviorMediaOrganizerApp):
    MIN_FOLDER_HEIGHT = 72
    MAX_FOLDER_HEIGHT = 420

    def __init__(self):
        super().__init__()
        self.folder_canvas.configure(height=132)
        self.resize_start_y = 0
        self.resize_start_height = 132
        self.resize_grip = ttk.Frame(self.preview, height=12, cursor='sb_v_double_arrow')
        self.resize_grip.pack(fill='x', padx=8, pady=(0, 2), before=self.tree)
        self.resize_grip.pack_propagate(False)
        ttk.Separator(self.resize_grip, orient='horizontal').pack(fill='x', pady=(2, 0))
        ttk.Label(self.resize_grip, text='↕ 拖动这里调整文件夹与素材列表的高度', anchor='center', foreground='#777', cursor='sb_v_double_arrow').pack(fill='x')
        self.resize_grip.bind('<ButtonPress-1>', self.start_panel_resize)
        self.resize_grip.bind('<B1-Motion>', self.resize_panels)
        for child in self.resize_grip.winfo_children():
            child.bind('<ButtonPress-1>', self.start_panel_resize)
            child.bind('<B1-Motion>', self.resize_panels)
        self.bind_folder_mousewheel()

    def start_panel_resize(self, event):
        if not self.folders_expanded.get(): self.toggle_folders()
        self.resize_start_y = event.y_root
        self.resize_start_height = int(float(self.folder_canvas.cget('height')))

    def resize_panels(self, event):
        height = self.resize_start_height + (event.y_root - self.resize_start_y)
        height = max(self.MIN_FOLDER_HEIGHT, min(self.MAX_FOLDER_HEIGHT, height))
        self.folder_canvas.configure(height=height)
        self.folder_area.update_idletasks()
        self.drag_hint.set(f'文件夹区域高度：{height}px · 可继续拖动边界调整')

    def on_folder_mousewheel(self, event):
        if not self.folders_expanded.get(): return 'break'
        delta = -1 if event.delta > 0 else 1
        self.folder_canvas.yview_scroll(delta * 3, 'units')
        return 'break'

    def bind_folder_mousewheel(self):
        widgets = [self.folder_canvas, self.folder_cards, self.folder_canvas.master]
        widgets.extend(self.folder_cards.winfo_children())
        for widget in widgets:
            widget.bind('<MouseWheel>', self.on_folder_mousewheel, add='+')

    def rebuild_folder_cards(self):
        super().rebuild_folder_cards()
        if hasattr(self, 'resize_grip'): self.bind_folder_mousewheel()


ResizablePanelsMediaOrganizerApp().mainloop()
