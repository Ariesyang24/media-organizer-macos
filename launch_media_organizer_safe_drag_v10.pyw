import builtins
import sys
from pathlib import Path
from tkinter import filedialog, ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_safe_drag_v9.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV9MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV9MediaOrganizerApp = scope['SafeDragV9MediaOrganizerApp']


class SafeDragV10MediaOrganizerApp(SafeDragV9MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.output_bar = ttk.Frame(self.preview, padding=(8, 3))
        before = getattr(self, 'more_bar', None) or getattr(self, 'folder_area', None)
        pack_options = {'fill': 'x'}
        if before is not None:
            pack_options['before'] = before
        self.output_bar.pack(**pack_options)
        ttk.Label(self.output_bar, text='整理保存位置：').pack(side='left')
        self.output_entry = ttk.Entry(self.output_bar, textvariable=self.out)
        self.output_entry.pack(side='left', fill='x', expand=True, padx=(4, 6))
        ttk.Button(self.output_bar, text='浏览…', command=self.choose_output_from_preview).pack(side='left')

    def choose_output_from_preview(self):
        selected = filedialog.askdirectory(title='选择整理后的保存位置', initialdir=self.out.get() or None, parent=self)
        if selected:
            self.out.set(selected)
            self.status.set(f'整理保存位置已更改：{selected}')


SafeDragV10MediaOrganizerApp().mainloop()
