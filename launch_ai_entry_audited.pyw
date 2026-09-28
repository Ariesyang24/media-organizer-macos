import builtins
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

root = Path(__file__).resolve().parent
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

final_path = root / 'launch_ai_entry_final.pyw'
source = final_path.read_text(encoding='utf-8').rsplit('AIEntryApp().mainloop()', 1)[0]
scope = {'__file__': str(final_path)}
exec(compile(source, str(final_path), 'exec'), scope)
AIEntryApp = scope['AIEntryApp']


class AuditedAIApp(AIEntryApp):
    def start_scan(self):
        if not self.sources:
            return messagebox.showwarning('提示', '请先添加素材来源')
        self.stop.clear()
        self.status.set('正在扫描识别…')
        option_names = ('smart', 'faces_on', 'video_on', 'scene_on')
        frozen = {}
        for name in option_names:
            variable = getattr(self, name, None)
            if variable is not None:
                frozen[name] = variable.get()
        output_path = self.out.get()

        def worker():
            patched = []
            try:
                self.out.get = lambda: output_path
                patched.append(self.out)
                for name, value in frozen.items():
                    variable = getattr(self, name)
                    variable.get = lambda saved=value: saved
                    patched.append(variable)
                AIEntryApp.scan(self)
            except Exception as exc:
                self.after(0, lambda error=exc: self.status.set(f'扫描中断：{error}'))
            finally:
                for variable in patched:
                    if 'get' in variable.__dict__:
                        del variable.__dict__['get']

        threading.Thread(target=worker, daemon=True).start()

    def render(self):
        for row in self.rows:
            analysis = row.get('analysis')
            if analysis and analysis.get('blur') is None:
                analysis['blur'] = 0.0
            video = row.get('video_analysis')
            if video and video.get('blur') is None:
                video['blur'] = 0.0
        super().render()


AuditedAIApp().mainloop()
