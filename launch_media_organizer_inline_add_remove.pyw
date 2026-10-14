import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_collapsible_sidebar.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('CollapsibleSidebarMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
CollapsibleSidebarMediaOrganizerApp = scope['CollapsibleSidebarMediaOrganizerApp']


class InlineAddRemoveMediaOrganizerApp(CollapsibleSidebarMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self._hide_old_list_buttons()
        self.source_controls = self._add_inline_controls(self.src_box, self.add_source, self.remove_source)
        self.exclude_controls = self._add_inline_controls(self.exc_box, self.add_exclusion, self.remove_exclusion)
        self.src_box.bind('<<ListboxSelect>>', lambda _event: self.update_inline_controls(), add='+')
        self.exc_box.bind('<<ListboxSelect>>', lambda _event: self.update_inline_controls(), add='+')
        self.update_inline_controls()

    def _hide_old_list_buttons(self):
        for widget in self.setup.winfo_children():
            self._hide_button_frame(widget)

    def _hide_button_frame(self, widget):
        children = widget.winfo_children()
        texts = []
        for child in children:
            try:
                if child.winfo_class() == 'TButton': texts.append(str(child.cget('text')))
            except Exception: pass
        if any('添加文件夹' in text or '添加排除目录' in text for text in texts) and any('移除选中' in text for text in texts):
            widget.pack_forget()
            return
        for child in children: self._hide_button_frame(child)

    def _add_inline_controls(self, box, add_command, remove_command):
        center_add = ttk.Button(box, text='＋', width=5, command=add_command)
        top_add = ttk.Button(box, text='＋', width=3, command=add_command)
        top_remove = ttk.Button(box, text='－', width=3, command=remove_command)
        return {'center': center_add, 'add': top_add, 'remove': top_remove}

    def update_inline_controls(self):
        for box, controls in ((self.src_box, self.source_controls), (self.exc_box, self.exclude_controls)):
            size = box.size()
            if size == 0:
                controls['add'].place_forget(); controls['remove'].place_forget()
                controls['center'].place(relx=0.5, rely=0.5, anchor='center', width=72, height=54)
            else:
                controls['center'].place_forget()
                controls['remove'].place(relx=1.0, x=-8, y=6, anchor='ne', width=38, height=30)
                controls['add'].place(relx=1.0, x=-50, y=6, anchor='ne', width=38, height=30)
                controls['remove'].configure(state='normal' if box.curselection() else 'disabled')

    def add_source(self):
        super().add_source(); self.update_inline_controls()

    def remove_source(self):
        super().remove_source(); self.update_inline_controls()

    def add_exclusion(self):
        super().add_exclusion(); self.update_inline_controls()

    def remove_exclusion(self):
        super().remove_exclusion(); self.update_inline_controls()

    def drop_src(self, event):
        result = super().drop_src(event); self.after_idle(self.update_inline_controls); return result

    def drop_exc(self, event):
        result = super().drop_exc(event); self.after_idle(self.update_inline_controls); return result


InlineAddRemoveMediaOrganizerApp().mainloop()
