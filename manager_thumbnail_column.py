import os
import threading
from PIL import Image, ImageTk
from thumbnail_gallery import make_thumbnail


class ManagerThumbnailColumn:
    def __init__(self, owner, tree, rows):
        self.owner = owner
        self.tree = tree
        self.rows = rows
        self.images = {}
        self.generation = 0
        tree.configure(show='tree headings')
        tree.heading('#0', text='预览')
        tree.column('#0', width=104, minwidth=104, stretch=False, anchor='center')
        tree.bind('<Double-1>', self.open_original, add='+')
        try:
            import tkinter.ttk as ttk
            ttk.Style(owner).configure('Manager.Treeview', rowheight=68)
            tree.configure(style='Manager.Treeview')
        except Exception:
            pass

    def refresh(self):
        self.generation += 1
        token = self.generation
        self.images.clear()
        items = []
        for iid in self.tree.get_children(''):
            try: items.append((iid, self.rows[int(iid)]))
            except (ValueError, IndexError): pass
        threading.Thread(target=self._load, args=(items, token), daemon=True).start()

    def _load(self, items, token):
        for iid, row in items:
            if token != self.generation: return
            path = make_thumbnail(row, size=(88, 58))
            self.owner.after(0, lambda i=iid, p=path, t=token: self._set(i, p, t))

    def _set(self, iid, path, token):
        if token != self.generation or not self.tree.exists(iid): return
        image = Image.open(path).copy(); image.thumbnail((88, 58), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image); self.images[iid] = photo
        self.tree.item(iid, image=photo)

    def open_original(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            try: os.startfile(str(self.rows[int(iid)]['p']))
            except (ValueError, IndexError, OSError): pass
