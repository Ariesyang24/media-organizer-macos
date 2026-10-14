import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_list_toolbar_fixed.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('ListToolbarFixedMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
ListToolbarFixedMediaOrganizerApp = scope['ListToolbarFixedMediaOrganizerApp']


class ListToolbarFinalMediaOrganizerApp(ListToolbarFixedMediaOrganizerApp):
    def update_inline_controls(self):
        if not hasattr(self, 'source_toolbar'):
            return super().update_inline_controls()
        for box, controls, toolbar in (
            (self.src_box, self.source_controls, self.source_toolbar),
            (self.exc_box, self.exclude_controls, self.exclude_toolbar),
        ):
            for button in controls.values():
                button.place_forget()
            toolbar['frame'].pack_forget()
            toolbar['frame'].place_forget()
            if box.size() == 0:
                box.pack_configure(pady=8)
                controls['center'].place(relx=0.5, rely=0.5, anchor='center', width=72, height=54)
            else:
                controls['center'].place_forget()
                box.pack_configure(pady=(42, 8))
                toolbar['frame'].place(relx=0, y=0, relwidth=1, height=32)
                toolbar['remove'].configure(state='normal' if box.curselection() else 'disabled')
                toolbar['frame'].lift()


ListToolbarFinalMediaOrganizerApp().mainloop()
