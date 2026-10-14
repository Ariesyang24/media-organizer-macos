import builtins
import sys
from pathlib import Path
from tkinter import ttk

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_safe_drag_v15.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV15MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV15MediaOrganizerApp = scope['SafeDragV15MediaOrganizerApp']


class SafeDragV16MediaOrganizerApp(SafeDragV15MediaOrganizerApp):
    COLUMN_WIDTHS = {
        'file': (210, 120),
        'date': (92, 82),
        'place': (105, 80),
        'device': (190, 120),
        'kind': (62, 52),
        'quality': (145, 100),
        'duplicate': (82, 65),
        'burst': (82, 65),
        'people': (150, 100),
        'recommend': (105, 75),
        'target': (390, 180),
        'video': (250, 150),
        'ai_scene': (180, 120),
    }

    def __init__(self):
        super().__init__()
        self._configure_review_columns()
        self._install_table_horizontal_scrollbar()

    def _configure_review_columns(self):
        self.tree.column('#0', width=96, minwidth=76, stretch=False, anchor='center')
        for column in self.tree['columns']:
            width, minimum = self.COLUMN_WIDTHS.get(column, (130, 70))
            self.tree.column(column, width=width, minwidth=minimum, stretch=False, anchor='w')

    def _install_table_horizontal_scrollbar(self):
        self.table_horizontal_scrollbar = ttk.Scrollbar(
            self.tree.master,
            orient='horizontal',
            command=self.tree.xview,
        )
        self.tree.configure(xscrollcommand=self.table_horizontal_scrollbar.set)
        self.table_horizontal_scrollbar.pack(
            side='bottom',
            fill='x',
            padx=8,
            pady=(0, 3),
            before=self.tree,
        )


SafeDragV16MediaOrganizerApp().mainloop()
