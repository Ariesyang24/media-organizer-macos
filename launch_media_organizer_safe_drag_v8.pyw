import builtins
import sys
from pathlib import Path
from tkinter import messagebox, simpledialog

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
from material_folder_manager import save_material_folders, valid_folder_name
from project_folder_catalog import add_project_folder, load_project_folders, rename_project_folder

launcher = root / 'launch_media_organizer_safe_drag_v7.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV7MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV7MediaOrganizerApp = scope['SafeDragV7MediaOrganizerApp']


class SafeDragV8MediaOrganizerApp(SafeDragV7MediaOrganizerApp):
    def folder_names(self):
        names = set(load_project_folders(getattr(self, 'sources', [])))
        names.update(row.get('custom_folder', '') for row in self.rows if row.get('custom_folder'))
        return sorted(names)

    def new_folder_for_selection(self):
        name = valid_folder_name(simpledialog.askstring('新建素材文件夹', '文件夹名称：', parent=self))
        if not name:
            messagebox.showinfo('名称不可用', '请输入有效名称，且不要包含 \\ / : * ? " < > |。', parent=self)
            return
        add_project_folder(getattr(self, 'sources', []), name)
        rows = self.selected_rows()
        if rows:
            self.assign_rows(rows, name)
            self.status.set(f'已新建“{name}”，并放入 {len(rows)} 个选中素材')
        else:
            self.folder_choice.set(name)
            self.refresh_folder_controls()
            self.rebuild_folder_cards()
            self.status.set(f'已新建当前项目文件夹“{name}”')

    def rename_custom_folder(self, old):
        new = valid_folder_name(simpledialog.askstring('重命名自定义文件夹', '新的文件夹名称：', initialvalue=old, parent=self))
        if not new or new == old:
            return
        rename_project_folder(getattr(self, 'sources', []), old, new)
        changed = set()
        for row in self.rows:
            if row.get('custom_folder') == old:
                row['custom_folder'] = new
                changed.add(str(row['p']))
        if changed:
            save_material_folders(self.rows, changed)
        self.render()
        self.folder_choice.set(new)
        self.refresh_folder_controls()
        self.status.set(f'已将自定义文件夹“{old}”重命名为“{new}”')

    def refresh_sidebar(self):
        super().refresh_sidebar()
        if not hasattr(self, 'sidebar_list') or not self.sidebar_targets:
            return
        selected_value = None
        current = self.sidebar_list.curselection()
        if current and current[0] < len(self.sidebar_targets):
            selected_value = self.sidebar_targets[current[0]]
        entries = [(target, self.sidebar_list.get(index)) for index, target in enumerate(self.sidebar_targets)]
        all_entries = [entry for entry in entries if entry[0][0] == 'all']
        custom_entries = [entry for entry in entries if entry[0][0] == 'empty' or (entry[0][0] == 'target' and '自定义分类' in Path(entry[0][1]).parts)]
        auto_entries = [entry for entry in entries if entry not in all_entries and entry not in custom_entries]
        ordered = all_entries + custom_entries + auto_entries
        self.sidebar_list.delete(0, 'end')
        self.sidebar_targets = []
        for target, label in ordered:
            self.sidebar_targets.append(target)
            self.sidebar_list.insert('end', label)
        wanted = selected_value or ('all', '')
        for index, target in enumerate(self.sidebar_targets):
            if target == wanted:
                self.sidebar_list.selection_set(index)
                self.sidebar_list.activate(index)
                self.sidebar_list.see(index)
                break


SafeDragV8MediaOrganizerApp().mainloop()
