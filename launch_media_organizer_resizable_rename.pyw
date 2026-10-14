import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_resizable_panels.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('ResizablePanelsMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
ResizablePanelsMediaOrganizerApp = scope['ResizablePanelsMediaOrganizerApp']


class ResizableRenameMediaOrganizerApp(ResizablePanelsMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        toolbar = self.compact_folder_box.master
        self.rename_folder_button = ttk.Button(toolbar, text='重命名文件夹', command=self.rename_selected_folder)
        self.rename_folder_button.pack(side='left', padx=(3, 0), after=self.compact_folder_box)
        self.folder_card_menu = tk.Menu(self, tearoff=False)
        self._bind_folder_card_menus()

    def rename_selected_folder(self):
        name = self.folder_choice.get().strip()
        if not name:
            messagebox.showinfo('请选择自建文件夹', '请先在“移入”下拉框中选择一个自建文件夹。', parent=self)
            return
        self.rename_custom_folder(name)

    def show_folder_card_menu(self, event, folder):
        self.folder_choice.set(folder)
        self.folder_card_menu.delete(0, 'end')
        self.folder_card_menu.add_command(label=f'重命名“{folder}”…', command=lambda: self.rename_custom_folder(folder))
        self.folder_card_menu.add_command(label='选择此文件夹素材', command=lambda: self.select_custom_folder_rows(folder))
        self.folder_card_menu.tk_popup(event.x_root, event.y_root)

    def _bind_folder_card_menus(self):
        if not hasattr(self, 'folder_cards'): return
        for card in self.folder_cards.winfo_children():
            folder = getattr(card, '_drop_folder', None)
            if folder and folder != '__AUTO__':
                card.bind('<Button-3>', lambda event, name=folder: self.show_folder_card_menu(event, name))

    def rebuild_folder_cards(self):
        super().rebuild_folder_cards()
        self._bind_folder_card_menus()


ResizableRenameMediaOrganizerApp().mainloop()
