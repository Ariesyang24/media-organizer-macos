import builtins
import sys
import tkinter as tk
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_contextual_plus.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('ContextualPlusMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
ContextualPlusMediaOrganizerApp = scope['ContextualPlusMediaOrganizerApp']


class FixedMinusColumnMediaOrganizerApp(ContextualPlusMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.source_minus_labels = []
        self.exclude_minus_labels = []
        for box in (self.src_box, self.exc_box):
            box.configure(activestyle='none')
            box.bind('<<ListboxSelect>>', lambda _event: self.after_idle(self._refresh_plain_minus), add='+')
            box.bind('<Configure>', lambda _event: self.after_idle(self._refresh_plain_minus), add='+')
            box.bind('<MouseWheel>', lambda _event: self.after_idle(self._refresh_plain_minus), add='+')
        self.after_idle(self._refresh_plain_minus)

    def _format_box(self, box, values):
        if box.size() != len(values):
            return
        selected = set(box.curselection())
        for index, value in enumerate(values):
            text = str(value)
            if box.get(index) != text:
                box.delete(index)
                box.insert(index, text)
        for index in selected:
            if index < box.size():
                box.selection_set(index)

    def _draw_minus_labels(self, box, storage, command):
        for label in storage:
            label.destroy()
        storage.clear()
        selected = set(box.curselection())
        for index in range(box.size()):
            bounds = box.bbox(index)
            if not bounds:
                continue
            _x, y, _width, height = bounds
            active = index in selected
            label = tk.Label(
                box, text='−', bd=0, relief='flat', highlightthickness=0,
                padx=0, pady=0, cursor='hand2',
                bg=box.cget('selectbackground') if active else box.cget('background'),
                fg=box.cget('selectforeground') if active else box.cget('foreground'),
            )
            label.place(relx=1.0, x=-14, y=y + height // 2, anchor='center', width=20, height=height)
            label.bind('<Button-1>', lambda _event, i=index, b=box, c=command: self._remove_label_row(b, i, c))
            storage.append(label)

    def _remove_label_row(self, box, index, command):
        box.selection_clear(0, 'end')
        box.selection_set(index)
        command()
        self.after_idle(self._refresh_plain_minus)
        return 'break'

    def _refresh_plain_minus(self):
        self._format_box(self.src_box, self.sources)
        self._format_box(self.exc_box, self.excludes)
        if hasattr(self, 'source_minus_labels'):
            self._draw_minus_labels(self.src_box, self.source_minus_labels, self.remove_source)
            self._draw_minus_labels(self.exc_box, self.exclude_minus_labels, self.remove_exclusion)


FixedMinusColumnMediaOrganizerApp().mainloop()
