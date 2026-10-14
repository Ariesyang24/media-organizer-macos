from launch_media_organizer_safe_drag_v44 import SafeDragV44MediaOrganizerApp
from locked_workspace_state_v45 import LockedWorkspaceStateV45
from recognition_page_state_v40 import WAITING, SCANNING, PAUSED, COMPLETED, FAILED


class SafeDragV45MediaOrganizerApp(SafeDragV44MediaOrganizerApp):
    def __init__(self):
        self.page_state=None
        super().__init__()
        self.page_state=LockedWorkspaceStateV45(self)


if __name__=='__main__':SafeDragV45MediaOrganizerApp().mainloop()
