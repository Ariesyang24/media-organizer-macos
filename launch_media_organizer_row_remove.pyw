import builtins
import sys
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_left_folders_only_v2.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('LeftFoldersOnlyV2MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
LeftFoldersOnlyV2MediaOrganizerApp = scope['LeftFoldersOnlyV2MediaOrganizerApp']


class RowRemoveMediaOrganizerApp(LeftFoldersOnlyV2MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.source_row_remove_buttons = []
        self.exclude_row_remove_buttons = []
        self.source_toolbar['remove'].pack_forget()
        self.exclude_toolbar['remove'].pack_forget()
        for box in (self.src_box, self.exc_box):
            box.bind('<Configure>', lambda _event: self.after_idle(self.update_row_remove_buttons), add='+')
            box.bind('<MouseWheel>', lambda _event: self.after_idle(self.update_row_remove_buttons), add='+')
            box.bind('<Button-4>', lambda _event: self.after_idle(self.update_row_remove_buttons), add='+')
            box.bind('<Button-5>', lambda _event: self.after_idle(self.update_row_remove_buttons), add='+')
        self.after_idle(self.update_row_remove_buttons)

    def _remove_one(self, box, index, command):
        box.selection_clear(0, 'end')
        box.selection_set(index)
        command()
        self.update_row_remove_buttons()

    def _build_row_buttons(self, box, storage, command):
        for button in storage:
            button.destroy()
        storage.clear()
        if box.size() == 0:
            return
        box.update_idletasks()
        for index in range(box.size()):
            bounds = box.bbox(index)
            if not bounds:
                continue
            _x, y, _width, height = bounds
            button = ttk.Button(
                box, text='－', width=2,
                command=lambda i=index, b=box, c=command: self._remove_one(b, i, c),
            )
            button.place(relx=1.0, x=-3, y=y, anchor='ne', width=34, height=max(20, height))
            storage.append(button)

    def update_row_remove_buttons(self):
        if not hasattr(self, 'source_row_remove_buttons'):
            return
        self._build_row_buttons(self.src_box, self.source_row_remove_buttons, self.remove_source)
        self._build_row_buttons(self.exc_box, self.exclude_row_remove_buttons, self.remove_exclusion)

    def update_inline_controls(self):
        super().update_inline_controls()
        if hasattr(self, 'source_toolbar'):
            self.source_toolbar['remove'].pack_forget()
            self.exclude_toolbar['remove'].pack_forget()
        if hasattr(self, 'source_row_remove_buttons'):
            self.after_idle(self.update_row_remove_buttons)


RowRemoveMediaOrganizerApp().mainloop()
