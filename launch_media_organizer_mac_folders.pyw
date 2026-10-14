import builtins
import sys
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

from folder_catalog import add_folder_to_catalog, load_folder_catalog, rename_folder_in_catalog
from material_folder_manager import save_material_folders, valid_folder_name

launcher = root / 'launch_media_organizer_compact_layout.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('CompactLayoutMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
CompactLayoutMediaOrganizerApp = scope['CompactLayoutMediaOrganizerApp']


class MacFolderBehaviorMediaOrganizerApp(CompactLayoutMediaOrganizerApp):
    def folder_names(self):
        names = set(load_folder_catalog())
        names.update(row.get('custom_folder', '') for row in self.rows if row.get('custom_folder'))
        return sorted(names)

    def new_folder_for_selection(self):
        name = valid_folder_name(simpledialog.askstring('新建素材文件夹', '文件夹名称：', parent=self))
        if not name:
            messagebox.showinfo('名称不可用', '请输入有效名称，且不要包含 \\ / : * ? " < > |。', parent=self)
            return
        add_folder_to_catalog(name)
        rows = self.selected_rows()
        if rows:
            self.assign_rows(rows, name)
            self.status.set(f'已新建“{name}”，并放入 {len(rows)} 个选中素材')
        else:
            self.folder_choice.set(name)
            self.refresh_folder_controls()
            self.rebuild_folder_cards()
            self.status.set(f'已新建空文件夹“{name}”；可拖入素材或使用“移入”')

    def rebuild_folder_cards(self):
        super().rebuild_folder_cards()
        existing = {getattr(card, '_drop_folder', None) for card in self.folder_cards.winfo_children()}
        empty_names = [name for name in self.folder_names() if name not in existing]
        start = len(self.folder_cards.winfo_children())
        for offset, name in enumerate(empty_names, start):
            text = f'★ 自定义 · 0 个素材\n日期 地点\\设备 类型\\自定义分类\\{name}'
            card = ttk.Button(self.folder_cards, text=text, command=lambda value=name: self.select_custom_folder_rows(value))
            card._drop_folder = name
            row_index, column = divmod(offset, 3)
            card.grid(row=row_index, column=column, sticky='nsew', padx=3, pady=3, ipadx=5, ipady=5)
        self._bind_folder_card_menus()
        names = self.folder_names()
        if hasattr(self, 'compact_folder_box'): self.compact_folder_box.configure(values=names)
        if hasattr(self, 'folder_box'): self.folder_box.configure(values=names)

    def rename_custom_folder(self, old):
        new = valid_folder_name(simpledialog.askstring('重命名自定义文件夹', '新的文件夹名称：', initialvalue=old, parent=self))
        if not new or new == old: return
        rename_folder_in_catalog(old, new)
        changed = set()
        for row in self.rows:
            if row.get('custom_folder') == old:
                row['custom_folder'] = new; changed.add(str(row['p']))
        if changed: save_material_folders(self.rows, changed)
        self.render(); self.folder_choice.set(new); self.refresh_folder_controls()
        self.status.set(f'已将自定义文件夹“{old}”重命名为“{new}”')


MacFolderBehaviorMediaOrganizerApp().mainloop()
