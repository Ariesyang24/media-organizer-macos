import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_safe_drag_v16.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV16MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV16MediaOrganizerApp = scope['SafeDragV16MediaOrganizerApp']


class SafeDragV17MediaOrganizerApp(SafeDragV16MediaOrganizerApp):
    COMPACT_COLUMN_WIDTHS = {
        'file': (180, 110),
        'date': (88, 78),
        'place': (92, 70),
        'device': (155, 105),
        'kind': (58, 50),
        'quality': (120, 88),
        'duplicate': (68, 58),
        'burst': (68, 58),
        'people': (105, 82),
        'recommend': (86, 68),
        'target': (300, 180),
        'video': (185, 125),
        'ai_scene': (125, 90),
    }

    def _configure_review_columns(self):
        self.tree.column('#0', width=84, minwidth=72, stretch=False, anchor='center')
        for column in self.tree['columns']:
            width, minimum = self.COMPACT_COLUMN_WIDTHS.get(column, (110, 65))
            self.tree.column(
                column,
                width=width,
                minwidth=minimum,
                stretch=(column == 'target'),
                anchor='w',
            )


SafeDragV17MediaOrganizerApp().mainloop()
