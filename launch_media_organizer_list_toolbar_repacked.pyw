import builtins
import sys
import tkinter as tk
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_list_toolbar_final.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('ListToolbarFinalMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
ListToolbarFinalMediaOrganizerApp = scope['ListToolbarFinalMediaOrganizerApp']


class ListToolbarRepackedMediaOrganizerApp(ListToolbarFinalMediaOrganizerApp):
    def update_inline_controls(self):
        if not hasattr(self, 'source_toolbar'):
            return super().update_inline_controls()
        rows = (
            (self.src_box, self.source_controls, self.source_toolbar, 'both', True),
            (self.exc_box, self.exclude_controls, self.exclude_toolbar, 'x', False),
        )
        for box, controls, toolbar, fill, expand in rows:
            try:
                if not box.winfo_exists() or not toolbar['frame'].winfo_exists():
                    continue
            except tk.TclError:
                continue
            for button in controls.values():
                try:
                    if button.winfo_exists(): button.place_forget()
                except tk.TclError: pass
            box.pack_forget()
            toolbar['frame'].pack_forget()
            toolbar['frame'].place_forget()
            if box.size() == 0:
                box.pack(fill=fill, expand=expand, pady=8)
                controls['center'].place(relx=0.5, rely=0.5, anchor='center', width=72, height=54)
            else:
                toolbar['frame'].pack(fill='x', pady=(8, 0))
                box.pack(fill=fill, expand=expand, pady=(4, 8))
                toolbar['remove'].configure(state='normal' if box.curselection() else 'disabled')


ListToolbarRepackedMediaOrganizerApp().mainloop()
