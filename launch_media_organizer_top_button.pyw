import builtins
from pathlib import Path

root = Path(__file__).resolve().parent
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

responsive_path = root / 'launch_media_organizer_responsive.pyw'
source = responsive_path.read_text(encoding='utf-8').rsplit('ResponsiveMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(responsive_path)}
exec(compile(source, str(responsive_path), 'exec'), scope)
ResponsiveMediaOrganizerApp = scope['ResponsiveMediaOrganizerApp']


class TopButtonMediaOrganizerApp(ResponsiveMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        bottom_button = self.scan_button
        bottom_button.pack_forget()
        self.action.configure(text='扫描并预览', command=self.start_scan, state='normal')
        self.action.pack(side='right', padx=(0, 8))
        self.scan_button = self.action
        self.status.set('添加素材后，点击右上角“扫描并预览”')


TopButtonMediaOrganizerApp().mainloop()
