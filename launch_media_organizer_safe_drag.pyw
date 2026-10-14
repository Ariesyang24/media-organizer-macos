import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_drag_feedback.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('DragFeedbackMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
DragFeedbackMediaOrganizerApp = scope['DragFeedbackMediaOrganizerApp']


class SafeDragMediaOrganizerApp(DragFeedbackMediaOrganizerApp):
    DRAG_THRESHOLD = 10

    def __init__(self):
        super().__init__()
        self.drag_press_point = None
        self.tree.bind('<ButtonPress-1>', self._remember_drag_press, add='+')

    def _remember_drag_press(self, event):
        row = self.tree.identify_row(event.y)
        self.drag_press_point = (event.x_root, event.y_root) if row else None

    def start_row_drag(self, event):
        if not self.tree.selection() or self.drag_press_point is None:
            return
        dx = event.x_root - self.drag_press_point[0]
        dy = event.y_root - self.drag_press_point[1]
        if not self.drag_active and dx * dx + dy * dy < self.DRAG_THRESHOLD * self.DRAG_THRESHOLD:
            return
        super().start_row_drag(event)

    def _sidebar_drop_target(self, index):
        if not (0 <= index < len(self.sidebar_targets)):
            return '__AUTO__', None
        kind, value = self.sidebar_targets[index]
        if kind == 'empty':
            return value, ('custom', value)
        if kind == 'target' and '自定义分类' in Path(value).parts:
            name = Path(value).parts[-1]
            return name, ('custom', name)
        return '__AUTO__', None

    def finish_row_drag(self, event):
        self.drag_press_point = None
        if not self.drag_active:
            self._destroy_drag_feedback()
            return
        rows = list(self.selected_rows())
        self._destroy_drag_feedback()
        self.drag_active = False
        self.tree.configure(cursor='')
        if not rows:
            return
        widget = self.winfo_containing(event.x_root, event.y_root)
        destination_filter = None
        folder = '__AUTO__'
        if widget is self.sidebar_list:
            local_y = event.y_root - self.sidebar_list.winfo_rooty()
            index = self.sidebar_list.nearest(local_y)
            bounds = self.sidebar_list.bbox(index)
            if bounds and bounds[1] <= local_y <= bounds[1] + bounds[3]:
                folder, destination_filter = self._sidebar_drop_target(index)
        self.drop_rows(rows, folder)

        if destination_filter is None:
            targets = {row.get('target', '') for row in rows if row.get('target')}
            self.current_folder_filter = next(iter(targets)) if len(targets) == 1 else None
        else:
            self.current_folder_filter = destination_filter
        self.refresh_sidebar()
        self.apply_filter()
        shown = len(self.tree.get_children(''))
        self.status.set(f'移动完成：{len(rows)} 个素材；已显示目标分类中的 {shown} 个素材')

    def match(self, row):
        folder_filter = getattr(self, 'current_folder_filter', None)
        if isinstance(folder_filter, tuple) and folder_filter[0] == 'custom':
            saved = self.current_folder_filter
            self.current_folder_filter = None
            try:
                base_match = super().match(row)
            finally:
                self.current_folder_filter = saved
            return base_match and row.get('custom_folder', '') == folder_filter[1]
        return super().match(row)

    def refresh_sidebar(self):
        super().refresh_sidebar()
        wanted = getattr(self, 'current_folder_filter', None)
        if not (isinstance(wanted, tuple) and wanted[0] == 'custom'):
            return
        name = wanted[1]
        for index, (kind, value) in enumerate(self.sidebar_targets):
            if kind == 'empty' and value == name:
                self.sidebar_list.selection_clear(0, 'end')
                self.sidebar_list.selection_set(index)
                self.sidebar_list.see(index)
                break
            if kind == 'target' and '自定义分类' in Path(value).parts and Path(value).parts[-1] == name:
                self.sidebar_list.selection_clear(0, 'end')
                self.sidebar_list.selection_set(index)
                self.sidebar_list.see(index)
                break


SafeDragMediaOrganizerApp().mainloop()
