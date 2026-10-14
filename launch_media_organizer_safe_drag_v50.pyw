import builtins, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scene-runtime'))
builtins.__file__=str(ROOT/'launch_scene_folder_final.pyw')
p=ROOT/'launch_media_organizer_safe_drag_v49.pyw'
scope={'__name__':'v50_base','__file__':str(p)}
exec(compile(p.read_text(encoding='utf-8-sig'),str(p),'exec'),scope)
Base=scope['SafeDragV49MediaOrganizerApp']
from workspace_interaction_v50 import WorkspaceInteractionV50

class SafeDragV50MediaOrganizerApp(Base):
    def __init__(self):
        super().__init__()
        self.workspace_interaction_v50=WorkspaceInteractionV50(self)

if __name__=='__main__':
    SafeDragV50MediaOrganizerApp().mainloop()
