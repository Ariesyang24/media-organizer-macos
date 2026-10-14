import os
import threading

from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

from thumbnail_gallery import make_thumbnail


class InlineThumbnailView(ttk.Frame):
    PAGE_SIZE = 60

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.rows = []
        self.loaded = 0
        self.generation = 0
        self.images = []
        self.selected = set()

        toolbar = ttk.Frame(self, padding=(4, 4, 4, 6))
        toolbar.pack(fill='x')
        self.summary = tk.StringVar(value='暂无素材')
        ttk.Label(toolbar, textvariable=self.summary, foreground='#555').pack(side='left')
        self.more = ttk.Button(toolbar, text='加载更多', command=self.load_more)
        self.more.pack(side='right')

        body = ttk.Frame(self)
        body.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(body, background='#f5f6f7', highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.grid = ttk.Frame(self.canvas, padding=6)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid, anchor='nw')
        self.grid.bind('<Configure>', lambda event: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', self._resize)
        self.canvas.bind('<MouseWheel>', self._wheel)
        for column in range(6):
            self.grid.columnconfigure(column, weight=1)

    def _resize(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _wheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), 'units')

    def refresh(self, rows):
        self.generation += 1
        self.rows = list(rows)
        self.loaded = 0
        self.images.clear()
        for child in self.grid.winfo_children():
            child.destroy()
        self.canvas.yview_moveto(0)
        self.load_more()

    def load_more(self):
        start = self.loaded
        end = min(len(self.rows), start + self.PAGE_SIZE)
        if start >= end:
            self._update_summary()
            return
        generation = self.generation
        batch = list(enumerate(self.rows[start:end], start))
        self.loaded = end
        self._update_summary()
        threading.Thread(target=self._prepare, args=(batch, generation), daemon=True).start()

    def _prepare(self, batch, generation):
        for index, (iid, row) in batch:
            if generation != self.generation:
                return
            path = make_thumbnail(row, size=(180, 110))
            self.after(0, lambda n=index, item=iid, data=row, thumb=path, token=generation: self._add_card(n, item, data, thumb, token))

    def _add_card(self, index, iid, row, thumb_path, generation):
        if generation != self.generation or not self.winfo_exists():
            return
        image = ImageTk.PhotoImage(Image.open(thumb_path))
        self.images.append(image)
        card = ttk.Frame(self.grid, padding=4, relief='ridge')
        card.grid(row=index // 6, column=index % 6, sticky='nsew', padx=4, pady=4)
        ttk.Button(card, image=image, command=lambda path=row['p']: os.startfile(str(path))).pack(fill='both', expand=True)
        name = row['p'].name
        ttk.Label(card, text=name if len(name) <= 22 else name[:19] + '…', anchor='center').pack(fill='x', pady=(4, 0))
        variable = tk.BooleanVar(value=str(iid) in self.app.tree.selection())
        ttk.Checkbutton(
            card,
            text='选择',
            variable=variable,
            command=lambda item=str(iid), value=variable: self._toggle(item, value.get()),
        ).pack(anchor='center')

    def _toggle(self, iid, enabled):
        if enabled:
            if self.app.tree.exists(iid):
                self.app.tree.selection_add(iid)
        else:
            self.app.tree.selection_remove(iid)

    def _update_summary(self):
        self.summary.set(f'缩略图已加载 {self.loaded}/{len(self.rows)} · 点击查看原始高清素材')
        if self.loaded >= len(self.rows):
            self.more.state(['disabled'])
        else:
            self.more.state(['!disabled'])
