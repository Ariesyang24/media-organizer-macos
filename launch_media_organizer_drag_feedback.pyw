import builtins
import sys
import tkinter as tk
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_sidebar_filter.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SidebarFilterMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SidebarFilterMediaOrganizerApp = scope['SidebarFilterMediaOrganizerApp']


class DragFeedbackMediaOrganizerApp(SidebarFilterMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.drag_ghost = None
        self.drag_ghost_image = None
        self.drag_hover_index = None
        self.drag_hover_colors = None
        self.bind('<Escape>', lambda _event: self.cancel_drag_feedback())

    def _create_drag_ghost(self, event):
        selected = self.tree.selection()
        if not selected or self.drag_ghost is not None:
            return
        ghost = tk.Toplevel(self)
        ghost.overrideredirect(True)
        try:
            ghost.attributes('-topmost', True)
            ghost.attributes('-alpha', 0.88)
        except tk.TclError:
            pass
        image = None
        if hasattr(self, 'tree_thumbnails'):
            image = self.tree_thumbnails.images.get(selected[0])
        self.drag_ghost_image = image
        text = f'  {len(selected)} 个素材' if len(selected) > 1 else '  移动素材'
        label = tk.Label(
            ghost, image=image, text=text, compound='left',
            bg='#ffffff', fg='#1f2937', bd=1, relief='solid',
            padx=8, pady=5, font=('Microsoft YaHei UI', 9, 'bold'),
        )
        label.pack()
        self.drag_ghost = ghost
        self._move_drag_ghost(event)

    def _move_drag_ghost(self, event):
        if self.drag_ghost is not None:
            self.drag_ghost.geometry(f'+{event.x_root + 18}+{event.y_root + 18}')

    def _clear_folder_hover(self):
        if self.drag_hover_index is None or not hasattr(self, 'sidebar_list'):
            return
        index = self.drag_hover_index
        if index < self.sidebar_list.size() and self.drag_hover_colors:
            background, foreground = self.drag_hover_colors
            self.sidebar_list.itemconfigure(index, background=background, foreground=foreground)
        self.drag_hover_index = None
        self.drag_hover_colors = None

    def _update_folder_hover(self, event):
        widget = self.winfo_containing(event.x_root, event.y_root)
        if widget is not self.sidebar_list:
            self._clear_folder_hover()
            return
        local_y = event.y_root - self.sidebar_list.winfo_rooty()
        index = self.sidebar_list.nearest(local_y)
        bounds = self.sidebar_list.bbox(index)
        if not bounds or not (bounds[1] <= local_y <= bounds[1] + bounds[3]):
            self._clear_folder_hover()
            return
        if index == self.drag_hover_index:
            return
        self._clear_folder_hover()
        self.drag_hover_index = index
        self.drag_hover_colors = (
            self.sidebar_list.itemcget(index, 'background'),
            self.sidebar_list.itemcget(index, 'foreground'),
        )
        self.sidebar_list.itemconfigure(index, background='#b9dcff', foreground='#073b66')
        if self.drag_ghost is not None:
            kind, value = self.sidebar_targets[index]
            target = '恢复自动分类' if kind == 'all' else (Path(value).name if kind == 'target' else value)
            self.drag_ghost.winfo_children()[0].configure(text=f'  放入：{target}')

    def start_row_drag(self, event):
        if not self.tree.selection():
            return
        if not self.drag_active:
            super().start_row_drag(event)
            self._create_drag_ghost(event)
        self._move_drag_ghost(event)
        self._update_folder_hover(event)

    def _destroy_drag_feedback(self):
        self._clear_folder_hover()
        if self.drag_ghost is not None:
            try:
                self.drag_ghost.destroy()
            except tk.TclError:
                pass
        self.drag_ghost = None
        self.drag_ghost_image = None

    def cancel_drag_feedback(self):
        self.drag_active = False
        self.tree.configure(cursor='')
        self._destroy_drag_feedback()
        self.status.set('已取消移动素材')

    def finish_row_drag(self, event):
        if not self.drag_active:
            return
        self._destroy_drag_feedback()
        super().finish_row_drag(event)


DragFeedbackMediaOrganizerApp().mainloop()
