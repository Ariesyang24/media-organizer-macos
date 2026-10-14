import builtins, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scene-runtime'))
builtins.__file__ = str(ROOT / 'launch_scene_folder_final.pyw')
launcher = ROOT / 'launch_media_organizer_safe_drag_v51.pyw'
scope = {'__name__': 'v52_base', '__file__': str(launcher)}
exec(compile(launcher.read_text(encoding='utf-8-sig'), str(launcher), 'exec'), scope)
Base = scope['SafeDragV51MediaOrganizerApp']


class SafeDragV52MediaOrganizerApp(Base):
    pass


if __name__ == '__main__':
    SafeDragV52MediaOrganizerApp().mainloop()
