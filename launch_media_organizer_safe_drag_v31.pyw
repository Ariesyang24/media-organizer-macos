import json
import builtins
import sys
from pathlib import Path
from tkinter import messagebox

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_safe_drag_v25.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV25MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV25MediaOrganizerApp = scope['SafeDragV25MediaOrganizerApp']


class SafeDragV26MediaOrganizerApp(SafeDragV25MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self._put_people_recognition_first()

    def _put_people_recognition_first(self):
        people = self._find_text_widget(self.preview, '模特识别并分类', 'TCheckbutton')
        quality = self._find_text_widget(self.preview, '画质/重复/连拍识别', 'TCheckbutton')
        if people is None or quality is None or people.master != quality.master:
            return
        manager = getattr(self, 'review_people_manager', None)
        people.pack_forget()
        quality.pack_forget()
        if manager is not None:
            manager.pack_forget()
        people.pack(side='left')
        quality.pack(side='left', padx=(12, 0))
        if manager is not None:
            manager.pack(side='left', padx=(8, 0))


class SafeDragV27MediaOrganizerApp(SafeDragV26MediaOrganizerApp):
    pass


class SafeDragV28MediaOrganizerApp(SafeDragV27MediaOrganizerApp):
    def _restore_saved_output_path(self):
        try:
            data = json.loads(self.SETTINGS_FILE.read_text(encoding='utf-8'))
            saved = str(data.get('output_path', '')).strip()
            path = Path(saved) if saved else None
            anchor = Path(path.anchor) if path and path.anchor else None
            if path and (not anchor or anchor.exists()):
                self.out.set(str(path))
                return
        except (OSError, ValueError, TypeError):
            pass
        pictures = Path.home() / 'Pictures'
        self.out.set(str(pictures / '所有素材'))


class SafeDragV29MediaOrganizerApp(SafeDragV28MediaOrganizerApp):
    OPTIONAL_QUALITY_COLUMNS = {'quality', 'duplicate', 'burst'}

    def __init__(self):
        super().__init__()
        self._sync_optional_columns()
        self.faces_on.trace_add('write', self._optional_columns_changed)
        self.smart.trace_add('write', self._optional_columns_changed)

    def _optional_columns_changed(self, *_args):
        self._sync_optional_columns()

    def _sync_optional_columns(self):
        columns = list(self.tree['columns'])
        visible = []
        for column in columns:
            if column == 'people' and not self.faces_on.get():
                continue
            if column in self.OPTIONAL_QUALITY_COLUMNS and not self.smart.get():
                continue
            visible.append(column)
        self.tree.configure(displaycolumns=tuple(visible))

    def _people_combined_changed(self):
        super()._people_combined_changed()
        self._sync_optional_columns()

    def render(self):
        self._sync_optional_columns()
        super().render()
        self._sync_optional_columns()

    def _show_progress(self, number, total, text):
        super()._show_progress(number, total, text)
        if not text.startswith('第二批识别'):
            return
        stages = []
        if self.smart.get():
            stages.append('画质、重复、连拍')
        if self.faces_on.get():
            stages.append('模特')
        stage = '与'.join(stages) if stages else '读取基础信息'
        percent = int(number * 100 / max(1, total))
        self.stage_text.set(f'当前阶段：{stage}  {number}/{total}  ({percent}%)')


class SafeDragV30MediaOrganizerApp(SafeDragV29MediaOrganizerApp):
    PREVIEW_COLUMN_WIDTH = 124

    def __init__(self):
        super().__init__()
        self._fix_preview_column_width()

    def _configure_review_columns(self):
        super()._configure_review_columns()
        self._fix_preview_column_width()

    def _fix_preview_column_width(self):
        if hasattr(self, 'tree'):
            self.tree.column('#0', width=self.PREVIEW_COLUMN_WIDTH,
                             minwidth=self.PREVIEW_COLUMN_WIDTH,
                             stretch=False, anchor='center')

    def render(self):
        self._fix_preview_column_width()
        super().render()
        self._fix_preview_column_width()


    def _remove_clipped_percent(self):
        text = self.stage_text.get()
        if '  (' in text:
            self.stage_text.set(text.rsplit('  (', 1)[0])

    def _show_progress(self, number, total, text):
        super()._show_progress(number, total, text)
        self._remove_clipped_percent()

    def _finish_scan(self, error):
        super()._finish_scan(error)
        self._remove_clipped_percent()

class SafeDragV31MediaOrganizerApp(SafeDragV30MediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self._replace_exclude_action()

    def _replace_exclude_action(self):
        for widget in self._descendants(self.preview):
            if widget.winfo_class() == 'TButton' and str(widget.cget('text')) == '排除选中':
                widget.configure(text='从整理中删除', command=self.remove_selected_from_plan)
                self.remove_from_plan_button = widget
                break

    def remove_selected_from_plan(self):
        if getattr(self, 'scan_busy', False):
            return messagebox.showinfo('正在识别', '请等待识别完成后再从整理中删除素材。', parent=self)
        indices=[]
        for iid in self.tree.selection():
            try:
                index=int(iid)
                if 0<=index<len(self.rows):indices.append(index)
            except (TypeError,ValueError):pass
        indices=sorted(set(indices),reverse=True)
        if not indices:
            return messagebox.showinfo('请先选择素材', '请选择一个或多个素材；可使用 Ctrl 或 Shift 批量选择。', parent=self)
        count=len(indices);names=[self.rows[index]['p'].name for index in reversed(indices)]
        preview='\n'.join(names[:5])
        if count>5:preview+=f'\n……另有 {count-5} 个素材'
        if not messagebox.askyesno('从本次整理中删除',f'确定从本次整理计划中删除 {count} 个素材吗？\n\n{preview}\n\n电脑中的原文件不会被删除。',parent=self):return
        removed=[]
        for index in indices:removed.append(self.rows.pop(index))
        if hasattr(self,'excluded'):self.excluded.extend(reversed(removed))
        self.calculate();self.render()
        if hasattr(self,'refresh_sidebar'):self.refresh_sidebar()
        if hasattr(self,'apply_filter'):self.apply_filter()
        self.status.set(f'已从本次整理中删除 {count} 个素材；电脑中的原文件保持不变')


SafeDragV31MediaOrganizerApp().mainloop()
