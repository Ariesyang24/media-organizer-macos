import tkinter as tk

from v3_ui_components import CanvasButton
from recognition_page_state_v40 import SCANNING, PAUSED, COMPLETED, FAILED
from state_adaptation_v41 import StateAdaptationV41


class StateActionsV42(StateAdaptationV41):
    """State-only copy and compact action placement for narrow windows."""

    def __init__(self, app):
        super().__init__(app)
        center = self.processing.body.winfo_children()[0]
        labels = [widget for widget in center.winfo_children() if isinstance(widget, tk.Label)]
        self.processing_title = tk.StringVar(value='正在生成分析结果')
        self.processing_help = tk.StringVar(value='已完成分析的素材会逐步显示在这里')
        labels[0].configure(textvariable=self.processing_title)
        labels[1].configure(textvariable=self.processing_help)

        self.compact_actions = tk.Frame(self.titleline.master, bg='white')
        self.compact_pause = CanvasButton(
            self.compact_actions, '暂停扫描', icon='pause', width=112, height=36,
            command=app.toggle_pause,
        )
        self.compact_stop = CanvasButton(
            self.compact_actions, '停止扫描', icon='stop', variant='danger', width=112, height=36,
            command=app.stop_scan,
        )
        self.compact_detail = CanvasButton(
            self.compact_actions, '查看详情', width=96, height=36, command=self.show_error,
        )
        self.compact_rescan = CanvasButton(
            self.compact_actions, '重新扫描', icon='rescan', variant='primary', width=112, height=36,
            command=app.start_scan,
        )
        self.compact_return = CanvasButton(
            self.compact_actions, '返回选择', icon='chevron-left', width=112, height=36,
            command=lambda: app._select_page(0),
        )
        self.apply(self.value.get(), self.error)

    def _hide_compact(self):
        if not hasattr(self, 'compact_actions'):
            return
        self.compact_actions.pack_forget()
        for button in self.compact_actions.winfo_children():
            button.pack_forget()

    def _show_compact(self, state):
        self._hide_compact()
        if state in (SCANNING, PAUSED):
            self.compact_pause.configure(
                text='暂停扫描' if state == SCANNING else '继续扫描',
                icon='pause' if state == SCANNING else 'play',
            )
            self.compact_pause.pack(side='left', padx=(0, 8))
            self.compact_stop.pack(side='left')
        elif state == COMPLETED:
            self.compact_rescan.pack(side='left')
        elif state == FAILED:
            self.compact_detail.pack(side='left', padx=(0, 8))
            self.compact_rescan.pack(side='left', padx=(0, 8))
            self.compact_return.pack(side='left')
        self.compact_actions.pack(fill='x', pady=(8, 0))

    def apply(self, state, error=''):
        super().apply(state, error)
        if not hasattr(self, 'processing_title'):
            return
        if state == SCANNING:
            self.processing_title.set('正在生成分析结果')
            self.processing_help.set('已完成分析的素材会逐步显示在这里')
        elif state == PAUSED:
            self.processing_title.set('扫描已暂停')
            self.processing_help.set('当前进度和已完成结果已保留')
        self.adapt()

    def adapt(self, event=None):
        super().adapt(event)
        if not hasattr(self, 'compact_actions'):
            return
        app = self.app
        state = self.value.get()
        if max(1, app.winfo_width()) <= 1320 and state in (SCANNING, PAUSED, COMPLETED, FAILED):
            app.pause_button.pack_forget()
            app.stop_scan_button.pack_forget()
            self.card_rescan.pack_forget()
            self.card_detail.pack_forget()
            self._show_compact(state)
        else:
            self._hide_compact()
