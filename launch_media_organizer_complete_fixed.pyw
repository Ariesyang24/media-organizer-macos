import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))

launcher = root / 'launch_media_organizer_complete.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('CompleteMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
scope['CompleteMediaOrganizerApp']().mainloop()
