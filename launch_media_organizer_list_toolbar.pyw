import builtins
import sys
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_setup_fixed.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SetupFixedMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SetupFixedMediaOrganizerApp = scope['SetupFixedMediaOrganizerApp']


class ListToolbarMediaOrganizerApp(SetupFixedMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        for controls in (self.source_controls, self.exclude_controls):
            for button in controls.values(): button.place_forget()
        self.source_toolbar = self._create_list_toolbar(self.src_box, self.add_source, self.remove_source)
        self.exclude_toolbar = self._create_list_toolbar(self.exc_box, self.add_exclusion, self.remove_exclusion)
        self.update_inline_controls()

    def _create_list_toolbar(self, box, add_command, remove_command):
        toolbar = ttk.Frame(box.master)
        ttk.Label(toolbar, text='文件夹列表', foreground='#666').pack(side='left')
        remove = ttk.Button(toolbar, text='－', width=3, command=remove_command)
        remove.pack(side='right')
        add = ttk.Button(toolbar, text='＋', width=3, command=add_command)
        add.pack(side='right', padx=(0, 4))
        return {'frame': toolbar, 'add': add, 'remove': remove, 'box': box}

    def update_inline_controls(self):
        if not hasattr(self, 'source_toolbar'):
            return super().update_inline_controls()
        for box, controls, toolbar in (
            (self.src_box, self.source_controls, self.source_toolbar),
            (self.exc_box, self.exclude_controls, self.exclude_toolbar),
        ):
            for button in controls.values(): button.place_forget()
            if box.size() == 0:
                toolbar['frame'].pack_forget()
                controls['center'].place(relx=0.5, rely=0.5, anchor='center', width=72, height=54)
            else:
                controls['center'].place_forget()
                if not toolbar['frame'].winfo_manager():
                    toolbar['frame'].pack(fill='x', pady=(8, 0), before=box)
                toolbar['remove'].configure(state='normal' if box.curselection() else 'disabled')


ListToolbarMediaOrganizerApp().mainloop()
