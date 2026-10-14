import builtins
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_safe_drag_v20.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV20MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV20MediaOrganizerApp = scope['SafeDragV20MediaOrganizerApp']


class SafeDragV21MediaOrganizerApp(SafeDragV20MediaOrganizerApp):
    SETTINGS_FILE = root / 'media_organizer_user_settings.json'

    def __init__(self):
        super().__init__()
        self._output_save_job = None
        self._restore_saved_output_path()
        self.out.trace_add('write', self._schedule_output_path_save)
        self.protocol('WM_DELETE_WINDOW', self._close_with_settings_save)

    def _restore_saved_output_path(self):
        try:
            data = json.loads(self.SETTINGS_FILE.read_text(encoding='utf-8'))
            saved = str(data.get('output_path', '')).strip()
            if saved:
                self.out.set(saved)
        except (OSError, ValueError, TypeError):
            pass

    def _schedule_output_path_save(self, *_args):
        if self._output_save_job is not None:
            self.after_cancel(self._output_save_job)
        self._output_save_job = self.after(350, self._save_output_path)

    def _save_output_path(self):
        self._output_save_job = None
        value = self.out.get().strip()
        if not value:
            return
        try:
            existing = json.loads(self.SETTINGS_FILE.read_text(encoding='utf-8'))
            if not isinstance(existing, dict):
                existing = {}
        except (OSError, ValueError, TypeError):
            existing = {}
        existing['output_path'] = value
        try:
            self.SETTINGS_FILE.write_text(
                json.dumps(existing, ensure_ascii=False, indent=2),
                encoding='utf-8',
            )
        except OSError:
            pass

    def _close_with_settings_save(self):
        self._save_output_path()
        self.destroy()


SafeDragV21MediaOrganizerApp().mainloop()
