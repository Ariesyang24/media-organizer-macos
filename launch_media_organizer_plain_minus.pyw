import builtins
import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_left_folders_only_v2.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('LeftFoldersOnlyV2MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
LeftFoldersOnlyV2MediaOrganizerApp = scope['LeftFoldersOnlyV2MediaOrganizerApp']


class PlainMinusMediaOrganizerApp(LeftFoldersOnlyV2MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.source_toolbar['remove'].pack_forget()
        self.exclude_toolbar['remove'].pack_forget()
        self._restore_setup_list_positions()
        self.src_box.bind('<Button-1>', lambda event: self._plain_minus_click(event, self.src_box, self.remove_source), add='+')
        self.exc_box.bind('<Button-1>', lambda event: self._plain_minus_click(event, self.exc_box, self.remove_exclusion), add='+')
        self.src_box.bind('<Configure>', lambda _event: self.after_idle(self._refresh_plain_minus), add='+')
        self.exc_box.bind('<Configure>', lambda _event: self.after_idle(self._refresh_plain_minus), add='+')
        self.after_idle(self._refresh_plain_minus)

    def _restore_setup_list_positions(self):
        for box, toolbar, fill, expand in (
            (self.src_box, self.source_toolbar, 'both', True),
            (self.exc_box, self.exclude_toolbar, 'x', False),
        ):
            parent = box.master
            label = parent.winfo_children()[0]
            box.pack_forget()
            toolbar['frame'].pack_forget()
            toolbar['frame'].pack(fill='x', pady=(8, 0), after=label)
            toolbar['remove'].pack_forget()
            box.pack(fill=fill, expand=expand, pady=(4, 8), after=toolbar['frame'])

    def _display_value(self, box, value):
        font = tkfont.Font(font=box.cget('font'))
        available = max(120, box.winfo_width() - 24)
        minus_width = font.measure('  −')
        text = str(value)
        remaining = max(font.measure(' '), available - font.measure(text) - minus_width)
        spaces = max(1, remaining // max(1, font.measure(' ')))
        return f'{text}{" " * spaces}  −'

    def _format_box(self, box, values):
        if box.size() != len(values):
            return
        selected = set(box.curselection())
        for index, value in enumerate(values):
            display = self._display_value(box, value)
            if box.get(index) != display:
                box.delete(index)
                box.insert(index, display)
        for index in selected:
            if index < box.size():
                box.selection_set(index)

    def _refresh_plain_minus(self):
        try:
            if not self.winfo_exists() or not self.src_box.winfo_exists() or not self.exc_box.winfo_exists(): return
            self._format_box(self.src_box, self.sources)
            self._format_box(self.exc_box, self.excludes)
        except tk.TclError:
            return

    def _plain_minus_click(self, event, box, command):
        if event.x < box.winfo_width() - 48 or box.size() == 0:
            return None
        index = box.nearest(event.y)
        bounds = box.bbox(index)
        if not bounds or not (bounds[1] <= event.y <= bounds[1] + bounds[3]):
            return None
        box.selection_clear(0, 'end')
        box.selection_set(index)
        command()
        self.after_idle(self._refresh_plain_minus)
        return 'break'

    def update_inline_controls(self):
        try: super().update_inline_controls()
        except tk.TclError: return
        if hasattr(self, 'source_toolbar'):
            self.source_toolbar['remove'].pack_forget()
            self.exclude_toolbar['remove'].pack_forget()
            self._restore_setup_list_positions()
        if hasattr(self, 'sources'):
            self.after_idle(self._refresh_plain_minus)


PlainMinusMediaOrganizerApp().mainloop()
