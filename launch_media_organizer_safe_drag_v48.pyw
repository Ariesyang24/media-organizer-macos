import builtins, sys, tkinter as tk
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scene-runtime'))
builtins.__file__=str(ROOT/'launch_scene_folder_final.pyw')
p=ROOT/'launch_media_organizer_safe_drag_v47.pyw'
scope={'__name__':'v48_base','__file__':str(p)}
exec(compile(p.read_text(encoding='utf-8-sig'),str(p),'exec'),scope)
Base=scope['SafeDragV47MediaOrganizerApp']
from workspace_completion_v48 import WorkspaceCompletionV48

class SafeDragV48MediaOrganizerApp(Base):
    def __init__(self):
        super().__init__()
        self.workspace_completion_v48=WorkspaceCompletionV48(self)
        self.unified_workspace.refresh()

    def _v3_selection_changed(self, _event=None):
        selected=list(self.tree.selection())
        if hasattr(self,'v3_selection_text'):
            self.v3_selection_text.set(f'已选择 {len(selected)} 个素材')
        if getattr(self,'page_state',None) is not None and self.page_state.drawer is not None:
            try:
                if self.page_state.drawer.winfo_exists() and self.page_state.drawer_tab.get()=='素材详情':
                    self.page_state.open_drawer('素材详情')
            except tk.TclError:
                pass

if __name__=='__main__':
    SafeDragV48MediaOrganizerApp().mainloop()
