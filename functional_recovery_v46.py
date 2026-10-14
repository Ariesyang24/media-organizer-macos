from locked_workspace_state_v45 import LockedWorkspaceStateV45


class FunctionalRecoveryV46(LockedWorkspaceStateV45):
    """Reconnect legacy workflow hooks to the live unified-workspace controls."""

    def __init__(self, app):
        super().__init__(app)
        # The original toolbar is replaced by UnifiedAuditWorkspace.  Core scan
        # code still addresses execute_button_v3, so it must point at the live
        # replacement rather than the destroyed legacy canvas widget.
        app.execute_button_v3 = app.unified_workspace.execute_btn
