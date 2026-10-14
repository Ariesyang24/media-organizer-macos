import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_safe_drag.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragMediaOrganizerApp = scope['SafeDragMediaOrganizerApp']


class SafeDragV2MediaOrganizerApp(SafeDragMediaOrganizerApp):
    def _is_inside_material_table(self, widget):
        current = widget
        while current is not None:
            if current is self.tree:
                return True
            if current is self:
                break
            current = getattr(current, 'master', None)
        return False

    def finish_row_drag(self, event):
        self.drag_press_point = None
        if not self.drag_active:
            self._destroy_drag_feedback()
            return
        rows = list(self.selected_rows())
        widget = self.winfo_containing(event.x_root, event.y_root)
        self._destroy_drag_feedback()
        self.drag_active = False
        self.tree.configure(cursor='')
        if not rows:
            return

        # Releasing anywhere inside the material table cancels the drag.
        if self._is_inside_material_table(widget):
            self.status.set('已取消移动：素材仍保留在原文件夹')
            return

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


SafeDragV2MediaOrganizerApp().mainloop()
