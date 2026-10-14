import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_plain_minus.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('PlainMinusMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
PlainMinusMediaOrganizerApp = scope['PlainMinusMediaOrganizerApp']


class ContextualPlusMediaOrganizerApp(PlainMinusMediaOrganizerApp):
    def _restore_setup_list_positions(self):
        for box, toolbar, fill, expand in (
            (self.src_box, self.source_toolbar, 'both', True),
            (self.exc_box, self.exclude_toolbar, 'x', False),
        ):
            parent = box.master
            label = parent.winfo_children()[0]
            box.pack_forget()
            toolbar['frame'].pack_forget()
            toolbar['remove'].pack_forget()
            if box.size() == 0:
                box.pack(fill=fill, expand=expand, pady=8, after=label)
            else:
                toolbar['frame'].pack(fill='x', pady=(8, 0), after=label)
                toolbar['remove'].pack_forget()
                box.pack(fill=fill, expand=expand, pady=(4, 8), after=toolbar['frame'])


ContextualPlusMediaOrganizerApp().mainloop()
