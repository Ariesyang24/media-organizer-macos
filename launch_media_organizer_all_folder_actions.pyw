import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

from folder_path_overrides import apply_path_overrides, clear_path_overrides, rename_target_for_rows
from material_folder_manager import valid_folder_name

launcher = root / 'launch_media_organizer_resizable_rename.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('ResizableRenameMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
ResizableRenameMediaOrganizerApp = scope['ResizableRenameMediaOrganizerApp']


class AllFolderActionsMediaOrganizerApp(ResizableRenameMediaOrganizerApp):
    def calculate(self):
        super().calculate()
        apply_path_overrides(self.rows)

    def rebuild_folder_cards(self):
        super().rebuild_folder_cards()
        groups = self.output_directories()
        for card in self.folder_cards.winfo_children():
            text = str(card.cget('text'))
            target = next((value for value in groups if value in text), None)
            if not target: continue
            card._target_path = target
            card.bind('<Button-3>', lambda event, value=target: self.show_any_folder_menu(event, value))
        if hasattr(self, 'resize_grip'): self.bind_folder_mousewheel()

    def show_any_folder_menu(self, event, target):
        parts = Path(target).parts
        is_custom = '自定义分类' in parts
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label=f'重命名“{parts[-1]}”…', command=lambda: self.rename_output_folder(target))
        menu.add_command(label='选择此文件夹素材', command=lambda: self.select_directory_rows(target))
        if is_custom:
            menu.add_separator()
            menu.add_command(label='按自定义分类名称统一重命名', command=lambda: self.rename_custom_folder(parts[-1]))
        self.folder_card_menu = menu
        menu.tk_popup(event.x_root, event.y_root)

    def rename_output_folder(self, old_target):
        old_path = Path(old_target)
        new_name = valid_folder_name(simpledialog.askstring('重命名文件夹', '新的文件夹名称：', initialvalue=old_path.name, parent=self))
        if not new_name or new_name == old_path.name: return
        new_target = str(old_path.parent / new_name)
        changed = rename_target_for_rows(self.rows, old_target, new_target)
        if not changed:
            messagebox.showinfo('没有素材', '当前目录中没有可重命名的素材。', parent=self); return
        self.render()
        self.status.set(f'已重命名目录：{old_target} → {new_target}（{changed} 个素材）')

    def assign_rows(self, rows, folder):
        clear_path_overrides(rows)
        super().assign_rows(rows, folder)

    def drop_rows(self, rows, folder):
        clear_path_overrides(rows)
        super().drop_rows(rows, folder)


AllFolderActionsMediaOrganizerApp().mainloop()
