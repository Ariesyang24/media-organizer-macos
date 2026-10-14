import builtins
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scene-runtime'))
builtins.__file__ = str(ROOT / 'launch_scene_folder_final.pyw')
launcher = ROOT / 'launch_media_organizer_safe_drag_v36.pyw'
source = launcher.read_text(encoding='utf-8').rsplit(
    'SafeDragV36MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV36MediaOrganizerApp = scope['SafeDragV36MediaOrganizerApp']

from unified_audit_workspace import UnifiedAuditWorkspace


class SafeDragV37MediaOrganizerApp(SafeDragV36MediaOrganizerApp):
    """Unified scan, audit, classification and organize workbench."""

    def __init__(self):
        self.unified_workspace = None
        super().__init__()
        for widget in self._descendants(self.preview):
            if widget.winfo_class() == 'Label' and str(widget.cget('text')) == '扫描、识别并分类您的媒体素材':
                widget.configure(text='扫描、审核、分类并批量整理媒体素材')
        self.unified_workspace = UnifiedAuditWorkspace(self)
        # Final design keeps recognition settings in the main toolbar, not the sidebar.
        self.recognition_settings_button.pack_forget()
        self.after_idle(self.render)

    def match(self, row):
        if self.unified_workspace is not None:
            return self.unified_workspace.matches(row)
        return super().match(row)

    def render(self):
        super().render()
        if self.unified_workspace is not None:
            self.unified_workspace.refresh()

    def apply_filter(self):
        if self.unified_workspace is not None:
            self.unified_workspace.enrich()
        super().apply_filter()
        if self.unified_workspace is not None:
            self.unified_workspace.refresh()

    def _apply_column_visibility(self):
        if self.unified_workspace is not None:
            self.unified_workspace._configure_review_table()
            return
        return super()._apply_column_visibility()

    def open_category(self, category):
        if self.unified_workspace is not None and category.startswith('审核:'):
            self.unified_workspace.select_audit(category.split(':', 1)[1])
            return
        return super().open_category(category)

    def open_material_folders(self):
        self.unified_workspace.open_drawer('分类管理')

    def toggle_settings_drawer(self):
        if self.unified_workspace is not None:
            self.unified_workspace.open_drawer('识别设置')
        else:
            super().toggle_settings_drawer()

    def _open_batch_adjustment(self):
        self.unified_workspace.open_drawer('批量操作')

    def _finish_scan(self, error):
        super()._finish_scan(error)
        if error is None and not self.stop.is_set():
            self.pause_button.pack_forget()
            self.stop_scan_button.pack_forget()
        if self.unified_workspace is not None:
            self.unified_workspace.refresh()

    def start_scan(self):
        if self.unified_workspace is not None:
            self.unified_workspace._close_drawer()
        # Restore task controls for the new run.
        try:
            self.stop_scan_button.pack(side='right', padx=(8, 0))
            self.pause_button.pack(side='right', padx=(12, 0))
        except Exception:
            pass
        return super().start_scan()


SafeDragV37MediaOrganizerApp().mainloop()
