import builtins, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scene-runtime'))
builtins.__file__=str(ROOT/'launch_scene_folder_final.pyw')
p=ROOT/'launch_media_organizer_safe_drag_v48.pyw'
scope={'__name__':'v49_base','__file__':str(p)}
exec(compile(p.read_text(encoding='utf-8-sig'),str(p),'exec'),scope)
Base=scope['SafeDragV48MediaOrganizerApp']
from classification_pagination_v49 import ClassificationPaginationV49

class SafeDragV49MediaOrganizerApp(Base):
    def __init__(self):
        super().__init__()
        self.classification_pagination_v49=ClassificationPaginationV49(self)

if __name__=='__main__':
    SafeDragV49MediaOrganizerApp().mainloop()
