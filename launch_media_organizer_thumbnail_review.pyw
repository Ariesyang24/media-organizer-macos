import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

from inline_thumbnail_view import InlineThumbnailView

optional_path = root / 'launch_media_organizer_scene_optional.pyw'
source = optional_path.read_text(encoding='utf-8').rsplit('SceneOptionalMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(optional_path)}
exec(compile(source, str(optional_path), 'exec'), scope)
SceneOptionalMediaOrganizerApp = scope['SceneOptionalMediaOrganizerApp']


class ThumbnailReviewMediaOrganizerApp(SceneOptionalMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.thumbnail_view = InlineThumbnailView(self.preview, self)
        self.thumbnail_view.pack(fill='both', expand=True, padx=8, pady=(0, 6), before=self.tree)
        self.tree.pack_forget()
        self._thumbnail_refresh_pending = False
        self.status.set('结果默认使用分页缩略图预览；点击缩略图查看原始素材')

    def _schedule_thumbnail_refresh(self):
        if not hasattr(self, 'thumbnail_view') or self._thumbnail_refresh_pending:
            return
        self._thumbnail_refresh_pending = True
        self.after_idle(self._refresh_thumbnails)

    def _refresh_thumbnails(self):
        self._thumbnail_refresh_pending = False
        visible = []
        for iid in self.tree.get_children(''):
            try:
                visible.append((iid, self.rows[int(iid)]))
            except (ValueError, IndexError):
                pass
        self.thumbnail_view.refresh(visible)

    def render(self):
        super().render()
        self._schedule_thumbnail_refresh()

    def apply_filter(self):
        super().apply_filter()
        self._schedule_thumbnail_refresh()


ThumbnailReviewMediaOrganizerApp().mainloop()
