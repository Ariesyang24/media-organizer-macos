import tkinter.simpledialog
from pathlib import Path
from tkinterdnd2 import DND_FILES, TkinterDnD
from media_organizer_windows_final import FinalApp

class DragApp(FinalApp):
    def __init__(self):
        super().__init__()
        TkinterDnD._require(self)
        self.src_box.drop_target_register(DND_FILES)
        self.src_box.dnd_bind('<<DropEnter>>', self.drop_enter)
        self.src_box.dnd_bind('<<DropLeave>>', self.drop_leave)
        self.src_box.dnd_bind('<<Drop>>', self.drop_sources)
        self.exc_box.drop_target_register(DND_FILES)
        self.exc_box.dnd_bind('<<Drop>>', self.drop_exclusions)
        self.status.set('可点击添加，也可把一个或多个素材文件夹拖入左侧来源区域')

    def drop_enter(self, event):
        self.src_box.configure(background='#e8f2ff')
        self.status.set('松开鼠标即可添加素材文件夹')
        return event.action

    def drop_leave(self, event):
        self.src_box.configure(background='white')
        return event.action

    def dropped_paths(self, event):
        return [Path(value) for value in self.tk.splitlist(event.data)]

    def drop_sources(self, event):
        self.src_box.configure(background='white')
        added = 0
        for path in self.dropped_paths(event):
            if path.is_dir() and path not in self.sources:
                self.sources.append(path)
                self.src_box.insert('end', str(path))
                added += 1
        self.status.set(f'已通过拖放添加 {added} 个素材来源' if added else '未添加：请拖入文件夹，不能只拖入单个文件')
        return event.action

    def drop_exclusions(self, event):
        added = 0
        for path in self.dropped_paths(event):
            if path.is_dir() and path not in self.excludes:
                self.excludes.append(path)
                self.exc_box.insert('end', str(path))
                added += 1
        self.status.set(f'已通过拖放添加 {added} 个排除目录')
        return event.action

DragApp().mainloop()
