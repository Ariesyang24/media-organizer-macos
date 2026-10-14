import builtins
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

from material_folder_manager import save_material_folders

launcher = root / 'launch_media_organizer_drag_folders.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('DragFolderMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
DragFolderMediaOrganizerApp = scope['DragFolderMediaOrganizerApp']


class CompactLayoutMediaOrganizerApp(DragFolderMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.folder_area.configure(text='素材文件夹与批量调整')
        self.folder_bar.pack_forget()
        self.folder_body = self.folder_canvas.master
        self.folder_body.pack_forget()
        self.folders_expanded = tk.BooleanVar(value=False)
        self.advanced_expanded = tk.BooleanVar(value=False)
        self._build_compact_folder_toolbar()
        self._prepare_advanced_settings()
        self._bind_folder_card_menus()

    def _build_compact_folder_toolbar(self):
        toolbar = ttk.Frame(self.folder_area)
        toolbar.pack(fill='x', pady=(5, 0))
        ttk.Button(toolbar, text='+ 新建文件夹', command=self.new_folder_for_selection).pack(side='left')
        ttk.Label(toolbar, text='移入：').pack(side='left', padx=(8, 2))
        self.compact_folder_box = ttk.Combobox(toolbar, textvariable=self.folder_choice, state='readonly', width=16)
        self.compact_folder_box.pack(side='left')
        ttk.Button(toolbar, text='移入', command=self.move_selection_to_choice).pack(side='left', padx=3)
        ttk.Button(toolbar, text='移出', command=self.remove_selection_from_folder).pack(side='left')
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=8)
        ttk.Checkbutton(toolbar, text='批量选择', variable=self.batch_select_mode, command=self.update_selection_status).pack(side='left')
        ttk.Button(toolbar, text='全选', command=self.select_all_visible).pack(side='left', padx=3)
        ttk.Button(toolbar, text='清空', command=self.clear_selection).pack(side='left')
        ttk.Label(toolbar, textvariable=self.selection_text, foreground='#555').pack(side='left', padx=6)
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=8)
        ttk.Label(toolbar, text='地点：').pack(side='left')
        ttk.Entry(toolbar, textvariable=self.place, width=13).pack(side='left')
        ttk.Button(toolbar, text='应用', command=self.apply_place).pack(side='left', padx=3)
        ttk.Button(toolbar, text='恢复', command=self.restore_place).pack(side='left')
        self.folder_toggle = ttk.Button(toolbar, text='展开文件夹 ▾', command=self.toggle_folders)
        self.folder_toggle.pack(side='right')

    def _find_labeled_frame(self, text):
        for child in self.preview.winfo_children():
            try:
                if str(child.cget('text')) == text: return child
            except Exception: pass
        return None

    def _prepare_advanced_settings(self):
        self.advanced_widgets = []
        location = self._find_labeled_frame('批次地点修正')
        rename = self._find_labeled_frame('照片文件重命名（可选）')
        if location is not None: location.pack_forget()
        if rename is not None:
            rename.pack_forget(); self.advanced_widgets.append(rename)
        if hasattr(self, 'scene_panel'):
            info = self.scene_panel.pack_info()
            control_name = info.get('after')
            controls = self.scene_panel.master.nametowidget(control_name) if control_name else None
            self.scene_panel.pack_forget()
            if controls is not None:
                controls.pack_forget(); self.advanced_widgets.append(controls)
            self.advanced_widgets.append(self.scene_panel)
        self.more_bar = ttk.Frame(self.preview, padding=(8, 2))
        self.more_bar.pack(fill='x', before=self.folder_area)
        ttk.Button(self.more_bar, text='更多设置 ▸', command=self.toggle_advanced).pack(side='left')
        ttk.Label(self.more_bar, text='场景识别、照片重命名等按需展开', foreground='#666').pack(side='left', padx=8)

    def toggle_advanced(self):
        expanded = not self.advanced_expanded.get(); self.advanced_expanded.set(expanded)
        button = self.more_bar.winfo_children()[0]
        if expanded:
            button.configure(text='收起设置 ▾')
            for widget in self.advanced_widgets:
                if widget == getattr(self, 'scene_panel', None): widget.pack(fill='x', padx=8, pady=(0, 4), before=self.folder_area)
                else: widget.pack(fill='x', padx=8, pady=2, before=self.folder_area)
        else:
            button.configure(text='更多设置 ▸')
            for widget in self.advanced_widgets: widget.pack_forget()

    def toggle_folders(self):
        expanded = not self.folders_expanded.get(); self.folders_expanded.set(expanded)
        if expanded:
            self.folder_body.pack(fill='x', pady=(5, 0))
            self.folder_toggle.configure(text='收起文件夹 ▴')
        else:
            self.folder_body.pack_forget()
            self.folder_toggle.configure(text='展开文件夹 ▾')

    def rebuild_folder_cards(self):
        super().rebuild_folder_cards()
        if hasattr(self, 'compact_folder_box'):
            names = self.folder_names(); self.compact_folder_box.configure(values=names)
        self._bind_folder_card_menus()

    def _bind_folder_card_menus(self):
        if not hasattr(self, 'folder_cards'): return
        for card in self.folder_cards.winfo_children():
            folder = getattr(card, '_drop_folder', None)
            if folder and folder != '__AUTO__':
                card.bind('<Button-3>', lambda event, name=folder: self.show_folder_card_menu(event, name))

    def show_folder_card_menu(self, event, folder):
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label=f'重命名“{folder}”…', command=lambda: self.rename_custom_folder(folder))
        menu.add_command(label='选择此文件夹素材', command=lambda: self.select_custom_folder_rows(folder))
        menu.tk_popup(event.x_root, event.y_root)

    def rename_custom_folder(self, old):
        new = simpledialog.askstring('重命名自定义文件夹', '新的文件夹名称：', initialvalue=old, parent=self)
        from material_folder_manager import valid_folder_name
        new = valid_folder_name(new)
        if not new or new == old: return
        changed = set()
        for row in self.rows:
            if row.get('custom_folder') == old:
                row['custom_folder'] = new; changed.add(str(row['p']))
        if not changed:
            messagebox.showinfo('没有素材', '该文件夹当前没有素材。', parent=self); return
        save_material_folders(self.rows, changed)
        self.render(); self.folder_choice.set(new)
        self.status.set(f'已将自定义文件夹“{old}”重命名为“{new}”')

    def select_custom_folder_rows(self, folder):
        visible = set(self.tree.get_children(''))
        matches = [str(index) for index, row in enumerate(self.rows) if row.get('custom_folder') == folder and str(index) in visible]
        self.tree.selection_remove(*self.tree.selection())
        if matches: self.tree.selection_set(matches); self.tree.focus(matches[0]); self.tree.see(matches[0])
        self.update_selection_status()


CompactLayoutMediaOrganizerApp().mainloop()
