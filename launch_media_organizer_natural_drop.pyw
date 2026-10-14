import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_all_folder_actions.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('AllFolderActionsMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
AllFolderActionsMediaOrganizerApp = scope['AllFolderActionsMediaOrganizerApp']


class NaturalDropMediaOrganizerApp(AllFolderActionsMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.drag_hint.set('拖到自建文件夹可加入；拖到空白处或非文件夹位置可移出自定义文件夹')

    def rebuild_folder_cards(self):
        super().rebuild_folder_cards()
        for card in list(self.folder_cards.winfo_children()):
            if getattr(card, '_drop_folder', None) == '__AUTO__' and not getattr(card, '_target_path', None):
                card.destroy()
        if hasattr(self, 'resize_grip'): self.bind_folder_mousewheel()

    def finish_row_drag(self, event):
        if not self.drag_active: return
        self.drag_active = False; self.tree.configure(cursor='')
        rows = self.selected_rows()
        if not rows: return
        widget = self.winfo_containing(event.x_root, event.y_root)
        folder = self.folder_drop_value(widget)
        self.drop_rows(rows, folder if folder is not None else '__AUTO__')


NaturalDropMediaOrganizerApp().mainloop()
