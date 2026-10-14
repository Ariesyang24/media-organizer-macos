import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

from tree_thumbnail_column import TreeThumbnailColumn

safe_path = root / 'launch_media_organizer_safe_models.pyw'
source = safe_path.read_text(encoding='utf-8').rsplit("scope['ThumbnailReviewMediaOrganizerApp']().mainloop()", 1)[0]
safe_scope = {'__file__': str(safe_path)}
exec(compile(source, str(safe_path), 'exec'), safe_scope)
ThumbnailReviewMediaOrganizerApp = safe_scope['scope']['ThumbnailReviewMediaOrganizerApp']


class TableThumbnailMediaOrganizerApp(ThumbnailReviewMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.thumbnail_view.pack_forget()
        self.tree.pack(fill='both', expand=True, padx=8, pady=(0, 6))
        self.tree_thumbnails = TreeThumbnailColumn(self)
        self.status.set('表格已保留；最左侧缩略图会在后台逐个加载')

    def _schedule_thumbnail_refresh(self):
        if hasattr(self, 'tree_thumbnails'):
            self.after_idle(self.tree_thumbnails.refresh)

    def render(self):
        super().render()
        if hasattr(self, 'tree_thumbnails'):
            self.after_idle(self.tree_thumbnails.refresh)

    def apply_filter(self):
        super().apply_filter()
        if hasattr(self, 'tree_thumbnails'):
            self.after_idle(self.tree_thumbnails.refresh)


TableThumbnailMediaOrganizerApp().mainloop()
