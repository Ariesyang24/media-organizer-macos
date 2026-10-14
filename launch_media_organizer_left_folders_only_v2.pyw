import builtins
import sys
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_list_toolbar_repacked.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('ListToolbarRepackedMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
ListToolbarRepackedMediaOrganizerApp = scope['ListToolbarRepackedMediaOrganizerApp']


class LeftFoldersOnlyV2MediaOrganizerApp(ListToolbarRepackedMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        sidebar_top = self.sidebar.winfo_children()[0]
        count_label = sidebar_top.winfo_children()[-1]
        self.sidebar_add_button = ttk.Button(
            sidebar_top, text='＋', width=3, command=self.new_folder_for_selection
        )
        self.sidebar_add_button.pack(side='right', padx=(4, 2), before=count_label)

        self.folder_area.configure(text='批量调整')
        self.folder_body.pack_forget()
        self.folders_expanded.set(False)
        area_children = self.folder_area.winfo_children()
        if area_children:
            area_children[0].pack_forget()  # duplicate hint and directory count

        toolbar = next(
            (child for child in self.folder_area.winfo_children()
             if self.folder_toggle in child.winfo_children()),
            None,
        )
        self.batch_toolbar = toolbar
        if toolbar is not None:
            for widget in toolbar.winfo_children()[:6]:
                widget.pack_forget()
            self.folder_toggle.pack_forget()
        self.drag_hint.set('文件夹选择、拖放、新建与重命名统一在左侧完成')

    def toggle_folders(self):
        self.folder_body.pack_forget()
        self.folders_expanded.set(False)


LeftFoldersOnlyV2MediaOrganizerApp().mainloop()
