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


class LeftFoldersOnlyMediaOrganizerApp(ListToolbarRepackedMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self._move_folder_actions_to_sidebar()

    def _move_folder_actions_to_sidebar(self):
        # The left sidebar is now the single place for folder management.
        sidebar_top = self.sidebar.winfo_children()[0]
        self.sidebar_add_button = ttk.Button(
            sidebar_top, text='＋', width=3,
            command=self.new_folder_for_selection,
        )
        self.sidebar_add_button.pack(side='right', padx=(4, 2), before=self.sidebar_count.master.winfo_children()[-1])

        self.folder_area.configure(text='批量调整')
        self.folder_body.pack_forget()
        self.folders_expanded.set(False)

        # Hide the old card header (hint + duplicate directory count).
        area_children = self.folder_area.winfo_children()
        for child in area_children:
            if child is self.folder_body:
                continue
            descendants = child.winfo_children()
            if any(str(widget) == str(self.folder_toggle) for widget in descendants):
                self.batch_toolbar = child
            elif descendants and any(str(widget) == str(self.directory_count) for widget in descendants):
                pass
        # The original header is the first child and is no longer needed.
        if area_children:
            area_children[0].pack_forget()

        toolbar = getattr(self, 'batch_toolbar', None)
        if toolbar is None:
            toolbar = next((child for child in self.folder_area.winfo_children()
                            if self.folder_toggle in child.winfo_children()), None)
        if toolbar is not None:
            widgets = toolbar.winfo_children()
            # Old folder actions: new, destination label/list, rename/move-in/move-out.
            for widget in widgets[:7]:
                widget.pack_forget()
            self.folder_toggle.pack_forget()

        self.drag_hint.set('文件夹选择、拖放、新建与重命名统一在左侧完成')

    def toggle_folders(self):
        # Kept for inherited calls, but duplicate right-side cards stay hidden.
        self.folder_body.pack_forget()
        self.folders_expanded.set(False)


LeftFoldersOnlyMediaOrganizerApp().mainloop()
