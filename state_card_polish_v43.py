import tkinter as tk
from tkinter import messagebox

from recognition_page_state_v40 import SCANNING, PAUSED, COMPLETED, FAILED
from state_actions_v42 import StateActionsV42


class StateCardPolishV43(StateActionsV42):
    """Polishes only state-card actions, copy, and narrow More menu."""

    def __init__(self, app):
        super().__init__(app)
        for button in (
            self.compact_pause, self.compact_stop, self.compact_detail,
            self.compact_rescan, self.compact_return,
        ):
            button.configure(width=132, height=40)

    def _show_compact(self, state):
        self._hide_compact()
        if state in (SCANNING, PAUSED):
            self.compact_pause.configure(
                text='暂停扫描' if state == SCANNING else '继续扫描',
                icon='pause' if state == SCANNING else 'play',
                variant='secondary' if state == SCANNING else 'primary',
                width=132, height=40,
            )
            self.compact_stop.configure(variant='danger', width=132, height=40)
            self.compact_pause.pack(side='left', padx=(0, 12))
            self.compact_stop.pack(side='left')
        elif state == COMPLETED:
            self.compact_rescan.configure(variant='secondary', width=132, height=40)
            self.compact_rescan.pack(side='left')
        elif state == FAILED:
            self.compact_detail.configure(variant='secondary', width=132, height=40)
            self.compact_rescan.configure(variant='primary', width=132, height=40)
            self.compact_return.configure(variant='secondary', width=132, height=40)
            self.compact_detail.pack(side='left', padx=(0, 12))
            self.compact_rescan.pack(side='left', padx=(0, 12))
            self.compact_return.pack(side='left')
        self.compact_actions.pack(fill='x', pady=(10, 0))

    def apply(self, state, error=''):
        super().apply(state, error)
        if state == FAILED:
            # Failure information belongs to the top status card only.
            self.error_card.pack_forget()
            self.show(self.phase_row, fill='x', pady=(5, 4))
            self.app.v3_phase.set('失败阶段：扫描与分析')
            self.app.v3_progress_text.set('')
            self.app.v3_percent_text.set('')
            self.app.v3_task.set(str(error or '扫描任务执行失败'))
        self.adapt()

    def show_more(self):
        app = self.app
        workspace = app.unified_workspace
        selected = bool(app.tree.selection())
        app._popup_actions([
            ('智能审核', lambda: workspace.open_drawer('批量操作'), True),
            ('相似项分组', workspace.select_similar_group, True),
            ('移动到分类', lambda: workspace.open_drawer('分类管理'), True),
            ('识别设置', lambda: app.waiting_v38.open_settings(), True),
            ('导出审核报告', lambda: messagebox.showinfo('导出审核报告', '请选择导出位置。', parent=app), True),
            ('列设置', app._show_column_settings, True),
            ('打开原文件', app.open_original, selected),
            ('打开视频关键帧', app.open_keyframes, selected),
            ('从整理中移除', app.remove_selected_from_plan, selected and not app.scan_busy),
        ], workspace.more_btn)
