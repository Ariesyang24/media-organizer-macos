import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_resizable_table.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('ResizableTableMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
ResizableTableMediaOrganizerApp = scope['ResizableTableMediaOrganizerApp']


class SidebarFilterMediaOrganizerApp(ResizableTableMediaOrganizerApp):
    def __init__(self):
        self.current_folder_filter = None
        super().__init__()
        self.refresh_sidebar()

    def refresh_sidebar(self):
        if not hasattr(self, 'sidebar_list'):
            return
        super().refresh_sidebar()
        self.sidebar_targets.insert(0, ('all', ''))
        self.sidebar_list.insert(0, f'▣ 全部素材  ({len(self.rows)})')
        self.sidebar_count.set(str(len(self.sidebar_targets) - 1))
        self.sidebar_list.selection_clear(0, 'end')
        wanted = getattr(self, 'current_folder_filter', None)
        selected_index = 0
        if wanted is not None:
            for index, (kind, value) in enumerate(self.sidebar_targets):
                if kind == 'target' and value == wanted:
                    selected_index = index
                    break
                if kind == 'empty' and wanted == ('empty', value):
                    selected_index = index
                    break
        self.sidebar_list.selection_set(selected_index)
        self.sidebar_list.activate(selected_index)
        self.sidebar_list.see(selected_index)

    def sidebar_select(self, _event=None):
        selected = self.sidebar_list.curselection()
        if not selected or selected[0] >= len(self.sidebar_targets):
            return
        kind, value = self.sidebar_targets[selected[0]]
        if kind == 'all':
            self.current_folder_filter = None
            label = '全部素材'
        elif kind == 'target':
            self.current_folder_filter = value
            label = str(value)
        else:
            self.current_folder_filter = ('empty', value)
            label = f'{value}（空文件夹）'
        self.tree.selection_remove(*self.tree.selection())
        self.apply_filter()
        shown = len(self.tree.get_children(''))
        self.status.set(f'当前文件夹：{label}；右侧显示 {shown} 个素材')

    def sidebar_context_menu(self, event):
        index = self.sidebar_list.nearest(event.y)
        if index < 0 or index >= len(self.sidebar_targets):
            return
        if self.sidebar_targets[index][0] == 'all':
            return
        super().sidebar_context_menu(event)

    def match(self, row):
        if not super().match(row):
            return False
        folder_filter = getattr(self, 'current_folder_filter', None)
        if folder_filter is None:
            return True
        if isinstance(folder_filter, tuple) and folder_filter[0] == 'empty':
            return False
        return row.get('target', '') == folder_filter


SidebarFilterMediaOrganizerApp().mainloop()
