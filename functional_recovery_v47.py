import tkinter as tk

from functional_recovery_v46 import FunctionalRecoveryV46


class FunctionalRecoveryV47(FunctionalRecoveryV46):
    def adapt(self, event=None):
        try:
            if not self.app.winfo_exists():
                return
            super().adapt(event)
        except tk.TclError:
            return
