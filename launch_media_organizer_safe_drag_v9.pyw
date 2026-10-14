import builtins
import sys
from pathlib import Path
from tkinter import messagebox

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_safe_drag_v8.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV8MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV8MediaOrganizerApp = scope['SafeDragV8MediaOrganizerApp']


class SafeDragV9MediaOrganizerApp(SafeDragV8MediaOrganizerApp):
    def rename_selected_folder(self):
        selected = self.sidebar_list.curselection() if hasattr(self, 'sidebar_list') else ()
        if not selected or selected[0] >= len(self.sidebar_targets):
            messagebox.showinfo('请选择文件夹', '请先在左侧文件夹列表中选择要重命名的文件夹。', parent=self)
            return
        kind, value = self.sidebar_targets[selected[0]]
        if kind == 'all':
            messagebox.showinfo('不能重命名', '“全部素材”不是实际文件夹，请选择下方的文件夹。', parent=self)
            return
        if kind == 'empty':
            self.rename_custom_folder(value)
            return
        parts = Path(value).parts
        if '自定义分类' in parts:
            self.rename_custom_folder(parts[-1])
        else:
            self.rename_output_folder(value)


SafeDragV9MediaOrganizerApp().mainloop()
