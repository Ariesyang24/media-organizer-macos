import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

from person_group_manager import PersonGroupManager, apply_saved_person_labels
from tree_thumbnail_column import TreeThumbnailColumn

safe_path = root / 'launch_media_organizer_safe_models.pyw'
source = safe_path.read_text(encoding='utf-8').rsplit("scope['ThumbnailReviewMediaOrganizerApp']().mainloop()", 1)[0]
safe_scope = {'__file__': str(safe_path)}
exec(compile(source, str(safe_path), 'exec'), safe_scope)
ThumbnailReviewMediaOrganizerApp = safe_scope['scope']['ThumbnailReviewMediaOrganizerApp']


class PeopleManagerMediaOrganizerApp(ThumbnailReviewMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.thumbnail_view.pack_forget()
        self.tree.pack(fill='both', expand=True, padx=8, pady=(0, 6))
        self.tree_thumbnails = TreeThumbnailColumn(self)
        self._connect_people_button(self)
        self.status.set('人物识别完成后可打开“模特分类管理”查看、命名和纠错')

    def _connect_people_button(self, widget):
        for child in widget.winfo_children():
            try:
                if child.winfo_class() == 'TButton' and '选中人物组命名' in str(child.cget('text')):
                    child.configure(text='模特分类管理', command=self.open_people_manager)
            except Exception:
                pass
            self._connect_people_button(child)

    def open_people_manager(self):
        apply_saved_person_labels(self.rows)
        PersonGroupManager(self)

    def name_person(self):
        self.open_people_manager()

    def _schedule_thumbnail_refresh(self):
        if hasattr(self, 'tree_thumbnails'):
            self.after_idle(self.tree_thumbnails.refresh)

    def render(self):
        apply_saved_person_labels(self.rows)
        super().render()
        if hasattr(self, 'tree_thumbnails'):
            self.after_idle(self.tree_thumbnails.refresh)

    def apply_filter(self):
        super().apply_filter()
        if hasattr(self, 'tree_thumbnails'):
            self.after_idle(self.tree_thumbnails.refresh)


PeopleManagerMediaOrganizerApp().mainloop()
