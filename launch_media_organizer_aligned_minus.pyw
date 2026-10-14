import builtins
import sys
import unicodedata
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_contextual_plus.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('ContextualPlusMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
ContextualPlusMediaOrganizerApp = scope['ContextualPlusMediaOrganizerApp']


class AlignedMinusMediaOrganizerApp(ContextualPlusMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        for box in (self.src_box, self.exc_box):
            box.configure(font=('Consolas', 10), activestyle='none')
        self.after_idle(self._refresh_plain_minus)

    @staticmethod
    def _cell_width(text):
        return sum(2 if unicodedata.east_asian_width(char) in ('W', 'F') else 1 for char in text)

    def _display_value(self, box, value):
        text = str(value)
        box.update_idletasks()
        font = __import__('tkinter.font', fromlist=['Font']).Font(font=box.cget('font'))
        cell_pixels = max(1, font.measure('0'))
        target_cells = max(8, (box.winfo_width() - 30) // cell_pixels)
        padding = max(1, target_cells - self._cell_width(text) - 1)
        return f'{text}{" " * padding}−'


AlignedMinusMediaOrganizerApp().mainloop()
