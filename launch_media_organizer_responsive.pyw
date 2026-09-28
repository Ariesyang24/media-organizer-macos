import builtins
import threading
from pathlib import Path
from tkinter import messagebox

root = Path(__file__).resolve().parent
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

optimized_path = root / 'launch_media_organizer.pyw'
source = optimized_path.read_text(encoding='utf-8').rsplit('MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(optimized_path)}
exec(compile(source, str(optimized_path), 'exec'), scope)
MediaOrganizerApp = scope['MediaOrganizerApp']


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


class ResponsiveMediaOrganizerApp(MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.scan_busy = False
        self.action.pack_forget()
        self.scan_button = next(
            widget for widget in descendants(self.setup)
            if widget.winfo_class() == 'TButton' and str(widget.cget('text')).startswith('扫描并预览')
        )
        self.scan_button.configure(command=self.start_scan)
        self.status.set('添加素材后，点击右下角“扫描并预览”')

    def start_scan(self):
        if self.scan_busy:
            return
        if not self.sources:
            return messagebox.showwarning('提示', '请先添加素材来源')
        self.scan_busy = True
        self.stop.clear()
        self.scan_button.configure(text='正在扫描…', state='disabled')
        self.book.select(self.preview)
        self.progress.configure(mode='indeterminate', maximum=100, value=0)
        self.progress.start(12)
        self.status.set('正在准备扫描，请稍候…')

        option_names = ('smart', 'faces_on', 'video_on', 'scene_on')
        frozen = {}
        for name in option_names:
            variable = getattr(self, name, None)
            if variable is not None:
                frozen[name] = variable.get()
        output_path = self.out.get()

        def worker():
            patched = []
            error = None
            try:
                self.out.get = lambda: output_path
                patched.append(self.out)
                for name, value in frozen.items():
                    variable = getattr(self, name)
                    variable.get = lambda saved=value: saved
                    patched.append(variable)
                MediaOrganizerApp.scan(self)
            except Exception as exc:
                error = exc
            finally:
                for variable in patched:
                    if 'get' in variable.__dict__:
                        del variable.__dict__['get']
                self.after(0, lambda caught=error: self._finish_scan(caught))

        self.after(80, lambda: threading.Thread(target=worker, daemon=True).start())

    def update(self, number, total, text):
        self.after(0, lambda: self._show_progress(number, total, text))

    def _show_progress(self, number, total, text):
        if str(self.progress.cget('mode')) != 'determinate':
            self.progress.stop()
            self.progress.configure(mode='determinate')
        self.progress.configure(maximum=max(1, total), value=number)
        self.status.set(text)

    def _finish_scan(self, error):
        self.progress.stop()
        self.progress.configure(mode='determinate')
        self.scan_busy = False
        self.scan_button.configure(text='重新扫描', state='normal')
        if error is not None:
            self.status.set(f'扫描中断：{error}')
            messagebox.showerror('扫描未完成', str(error), parent=self)
        elif self.stop.is_set():
            self.status.set('扫描已停止，可修改选项后重新扫描')


ResponsiveMediaOrganizerApp().mainloop()
