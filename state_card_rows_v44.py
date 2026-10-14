from tkinter import messagebox
import tkinter as tk

from v3_ui_components import CanvasButton
from recognition_page_state_v40 import SCANNING, PAUSED, COMPLETED, FAILED
from state_card_polish_v43 import StateCardPolishV43


class StateCardRowsV44(StateCardPolishV43):
    """A dedicated, non-shrinking third row for state-card actions."""

    def __init__(self, app):
        super().__init__(app)
        app.progress_card_v3.configure(height=190)
        self.status_action_row = tk.Frame(app.progress_card_v3.body, bg='white', height=40)
        self.status_action_row.pack_propagate(False)
        self.action_pause = CanvasButton(
            self.status_action_row, '暂停扫描', icon='pause', variant='secondary',
            width=132, height=40, radius=8, command=app.toggle_pause,
        )
        self.action_stop = CanvasButton(
            self.status_action_row, '停止扫描', icon='stop', variant='danger',
            width=132, height=40, radius=8, command=app.stop_scan,
        )
        self.action_detail = CanvasButton(
            self.status_action_row, '查看详情', icon='info', variant='secondary',
            width=132, height=40, radius=8, command=self.show_error,
        )
        self.action_rescan = CanvasButton(
            self.status_action_row, '重新扫描', icon='rescan', variant='secondary',
            width=132, height=40, radius=8, command=app.start_scan,
        )
        self.action_return = CanvasButton(
            self.status_action_row, '返回选择', icon='chevron-left', variant='secondary',
            width=132, height=40, radius=8, command=lambda: app._select_page(0),
        )
        self.apply(self.value.get(), self.error)

    def _clear_all_state_actions(self):
        for widget in (
            self.app.pause_button, self.app.stop_scan_button, self.card_rescan, self.card_detail,
            self.compact_actions, self.status_action_row,
        ):
            widget.pack_forget()
        for button in self.status_action_row.winfo_children():
            button.pack_forget()

    def _show_state_actions(self, state):
        self._clear_all_state_actions()
        if state == SCANNING:
            self.action_pause.configure(text='暂停扫描', icon='pause', variant='secondary')
            self.action_pause.pack(side='left', padx=(0, 12)); self.action_stop.pack(side='left')
        elif state == PAUSED:
            self.action_pause.configure(text='继续扫描', icon='play', variant='nav-active')
            self.action_pause.pack(side='left', padx=(0, 12)); self.action_stop.pack(side='left')
        elif state == COMPLETED:
            self.action_rescan.configure(variant='secondary')
            self.action_rescan.pack(side='left')
        elif state == FAILED:
            self.action_detail.configure(variant='secondary')
            self.action_rescan.configure(variant='primary')
            self.action_return.configure(variant='secondary')
            self.action_detail.pack(side='left', padx=(0, 12))
            self.action_rescan.pack(side='left', padx=(0, 12))
            self.action_return.pack(side='left')
        self.status_action_row.pack(fill='x', pady=(12, 0))

    def apply(self, state, error=''):
        super().apply(state, error)
        if not hasattr(self, 'status_action_row'):
            return
        app = self.app
        app.progress_card_v3.configure(height=190)
        if state == SCANNING:
            app.v3_phase.set('AI识别与分类')
            self.processing_title.set('正在生成分析结果')
            self.processing_help.set('已完成分析的素材会逐步显示在这里')
        elif state == PAUSED:
            app.v3_phase.set('AI识别与分类')
            self.processing_title.set('扫描已暂停')
            self.processing_help.set('当前进度和已完成的分析结果已保留')
        elif state == COMPLETED:
            total = len(app.rows)
            app.v3_phase.set('全部完成')
            app.v3_progress_text.set(f'{total} / {total}')
            app.v3_percent_text.set('100%')
            app.v3_progress_value.set(100)
        elif state == FAILED:
            app.v3_phase.set('失败阶段：扫描与分析')
            app.v3_progress_text.set(''); app.v3_percent_text.set('')
            app.v3_task.set(str(error or '扫描任务执行失败'))
            self.error_card.pack_forget()
        self._show_state_actions(state)

    def adapt(self, event=None):
        super().adapt(event)
        if hasattr(self, 'status_action_row') and self.value.get() in (SCANNING, PAUSED, COMPLETED, FAILED):
            self._show_state_actions(self.value.get())

    def show_more(self):
        app = self.app; workspace = app.unified_workspace
        app._popup_actions([
            ('智能审核', lambda: workspace.open_drawer('批量操作'), True),
            ('相似项分组', workspace.select_similar_group, True),
            ('移动到分类', lambda: workspace.open_drawer('分类管理'), True),
            ('识别设置', lambda: app.waiting_v38.open_settings(), True),
            ('导出审核报告', workspace.export_review_report, True),
            ('列设置', app._show_column_settings, True),
        ], workspace.more_btn)
