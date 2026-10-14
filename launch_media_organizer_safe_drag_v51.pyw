import builtins, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scene-runtime'))
builtins.__file__=str(ROOT/'launch_scene_folder_final.pyw')
p=ROOT/'launch_media_organizer_safe_drag_v50.pyw'
scope={'__name__':'v51_base','__file__':str(p)}
exec(compile(p.read_text(encoding='utf-8-sig'),str(p),'exec'),scope)
Base=scope['SafeDragV50MediaOrganizerApp']
from embedded_workspace_drawer_v51 import EmbeddedWorkspaceDrawerV51

class SafeDragV51MediaOrganizerApp(Base):
    def __init__(self):
        super().__init__()
        self.embedded_workspace_drawer_v51=EmbeddedWorkspaceDrawerV51(self)

if __name__=='__main__':
    SafeDragV51MediaOrganizerApp().mainloop()
