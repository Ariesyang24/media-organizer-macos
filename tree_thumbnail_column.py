import os
import queue
import threading

from PIL import Image, ImageTk

from thumbnail_gallery import make_thumbnail


class TreeThumbnailColumn:
    def __init__(self, app):
        self.app = app
        self.tree = app.tree
        self.images = {}
        self.generation = 0
        # Tk calls are only legal on the main UI thread.  Thumbnail files may
        # be prepared in workers, but delivery to the Treeview is drained by
        # this queue from the event loop.
        self._ready = queue.Queue()
        self._poll_id = self.app.after(40, self._drain_ready)
        self.tree.configure(show='tree headings')
        self.tree.heading('#0', text='预览')
        self.tree.column('#0', width=96, minwidth=96, stretch=False, anchor='center')
        self.tree.bind('<ButtonRelease-1>', self._open_from_thumbnail, add='+')
        self.style = app.style if hasattr(app, 'style') else None
        try:
            import tkinter.ttk as ttk
            ttk.Style(app).configure('Treeview', rowheight=58)
        except Exception:
            pass

    def refresh(self):
        self.generation += 1
        token = self.generation
        self.images.clear()
        items = []
        for iid in self.tree.get_children(''):
            try:
                items.append((iid, self.app.rows[int(iid)]))
            except (ValueError, IndexError):
                pass
        threading.Thread(target=self._prepare, args=(items, token), daemon=True).start()

    def _prepare(self, items, token):
        for iid, row in items:
            if token != self.generation:
                return
            try:
                path = make_thumbnail(row, size=(80, 50))
            except Exception:
                continue
            self._ready.put((iid, path, token))

    def _drain_ready(self):
        try:
            if not self.app.winfo_exists():
                return
            while True:
                try:
                    iid, path, token = self._ready.get_nowait()
                except queue.Empty:
                    break
                self._set_image(iid, path, token)
            self._poll_id = self.app.after(40, self._drain_ready)
        except Exception:
            # The window may be in the middle of closing.  Do not let a late
            # thumbnail callback create a background-thread/Tk exception.
            return

    def _set_image(self, iid, thumb_path, token):
        try:
            if token != self.generation or not self.tree.winfo_exists() or not self.tree.exists(iid):
                return
            with Image.open(thumb_path) as source:
                image = source.copy()
            image.thumbnail((80, 50), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.images[iid] = photo
            self.tree.item(iid, image=photo)
        except Exception:
            return

    def _open_from_thumbnail(self, event):
        if self.tree.identify_column(event.x) != '#0':
            return
        iid = self.tree.identify_row(event.y)
        if iid:
            try:
                os.startfile(str(self.app.rows[int(iid)]['p']))
            except (ValueError, IndexError, OSError):
                pass
