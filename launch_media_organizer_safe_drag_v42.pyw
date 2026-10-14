from launch_media_organizer_safe_drag_v38 import MediaOrganizerV38
from state_actions_v42 import StateActionsV42


class MediaOrganizerV42(MediaOrganizerV38):
    def __init__(self):
        super().__init__()
        self.page_state = StateActionsV42(self)
        self.minsize(1100, 680)

    def toggle_pause(self):
        super().toggle_pause()
        self.page_state.apply('PAUSED' if self.scan_paused else 'SCANNING')


if __name__ == '__main__':
    app = MediaOrganizerV42()
    app.mainloop()
