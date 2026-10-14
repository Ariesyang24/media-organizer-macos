import builtins, os, shutil, sys, threading, time
from pathlib import Path
from tkinter import messagebox
from resumable_organizer import ResumableOrganizer, write_report
from media_organizer_windows import safe

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scene-runtime'))
builtins.__file__ = str(ROOT / 'launch_scene_folder_final.pyw')
launcher = ROOT / 'launch_media_organizer_safe_drag_v52.pyw'
scope = {'__name__': 'v53_base', '__file__': str(launcher)}
exec(compile(launcher.read_text(encoding='utf-8-sig'), str(launcher), 'exec'), scope)
Base = scope['SafeDragV52MediaOrganizerApp']


class SafeDragV53MediaOrganizerApp(Base):
    """Streams scan results into the workbench and opens media from the table."""

    def __init__(self):
        self._last_live_render = 0.0
        self.sidebar_manual_override = False
        super().__init__()
        self._remember_workspace_layout()
        # Keep the collapse control fully inside the sidebar.  Its old anchor
        # straddled the content boundary and could be covered by the page.
        self.collapse_button.place(relx=1.0, x=-8, y=16, anchor='ne')
        self._raise_sidebar_toggle()
        self.tree.bind('<Double-1>', self._open_clicked_media, add='+')
        self.tree.bind('<ButtonRelease-1>', self._open_preview_cell, add='+')

    def calculate(self):
        """Omit placeholder locations from generated output folder names."""
        super().calculate()
        for row in self.rows:
            place = str(row.get('place', '')).strip()
            if place not in {'', '未设置', '未知', '未知地点', 'Unknown', 'Unknown Location'}:
                continue
            target = Path(str(row.get('target', '')))
            parts = list(target.parts)
            if not parts:
                continue
            date = str(row.get('date', '')).replace('-', '.')
            # The base formatter may translate an empty location to either
            # "未知" or "Unknown".  The row value is the source of truth, so
            # remove any generated placeholder instead of matching its label.
            parts[0] = date
            row['target'] = str(Path(*parts))

    def _toggle_sidebar(self):
        self.sidebar_manual_override = True
        self._sidebar_transition_until = time.monotonic() + 0.22
        super()._toggle_sidebar()
        self._raise_sidebar_toggle()
        self.after(240, self._finish_sidebar_transition)

    def _finish_sidebar_transition(self):
        self._sidebar_transition_until = 0
        if self.folder_tree_panel.winfo_exists():
            self.folder_tree_panel.render()
        self._raise_sidebar_toggle()

    def _raise_sidebar_toggle(self):
        # CanvasButton inherits Canvas, whose lift() method raises canvas items
        # rather than the widget.  Raise the widget through Tk itself.
        self.tk.call('raise', self.collapse_button._w)

    def start_scan(self):
        result = super().start_scan()
        if self.scan_busy:
            # Paint the complete workbench and state actions before intensive
            # analysis callbacks begin arriving.  Without this flush, Canvas
            # controls can remain as blank background rectangles until a later
            # resize/repaint event, which looked like a skeleton UI.
            self._ensure_live_workspace()
            self.update_idletasks()
        return result

    def _remember_workspace_layout(self):
        content = self.waiting_v38.content
        self._workspace_children = list(content.pack_slaves())
        self._workspace_pack = {}
        for child in self._workspace_children:
            info = dict(child.pack_info())
            info.pop('in', None)
            self._workspace_pack[child] = info

    def _ensure_live_workspace(self):
        """Restore the one canonical workbench during scanning/paused states."""
        state = 'PAUSED' if self.scan_pause.is_set() else 'SCANNING'
        self.page_state.apply(state)
        content = self.waiting_v38.content
        if not content.winfo_manager():
            content.pack(fill='both', expand=True)
        for child in self._workspace_children:
            if child.winfo_exists() and not child.winfo_manager():
                child.pack(**self._workspace_pack[child])
        if self.rows:
            self.page_state._overlay()
        else:
            title = '扫描已暂停' if state == 'PAUSED' else '正在生成分析结果'
            help_text = ('当前进度和已完成的分析结果已保留' if state == 'PAUSED'
                         else '已完成分析的素材会逐步显示在这里')
            self.page_state._overlay(title, help_text)
            self.page_state.workspace_overlay.lift()
        self._raise_sidebar_toggle()

    def _show_progress(self, number, total, text):
        super()._show_progress(number, total, text)
        now = time.monotonic()
        if self.scan_busy:
            if self.rows and (number >= total or now - self._last_live_render >= 0.35):
                self._last_live_render = now
                self.render()
            self._ensure_live_workspace()

    def _row_from_event(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid or not str(iid).isdigit():
            return None
        index = int(iid)
        if not 0 <= index < len(self.rows):
            return None
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        return self.rows[index]

    def _open_media_row(self, row):
        path = Path(row['p'])
        if not path.exists():
            self.status.set(f'原文件不存在：{path}')
            return
        try:
            os.startfile(str(path))
            self.status.set(f'已打开：{path.name}')
        except OSError as exc:
            self.status.set(f'无法打开 {path.name}：{exc}')

    def _open_clicked_media(self, event):
        row = self._row_from_event(event)
        if row is not None:
            self._open_media_row(row)
            return 'break'

    def _open_preview_cell(self, event):
        if self.tree.identify_column(event.x) != '#0':
            return
        row = self._row_from_event(event)
        if row is not None:
            self.after_idle(lambda item=row: self._open_media_row(item))

    def full_run(self, out):
        """Run the final organize step with durable per-file checkpoints."""
        run_started = time.monotonic()
        out = Path(out)
        if self.rename_on.get() and self.rename_base.get().strip():
            groups = {}
            for row in self.rows:
                if row['kind'] == '照片':
                    groups.setdefault(row['target'], {}).setdefault(row['p'].stem, []).append(row)
            for target, stems in groups.items():
                ordered = sorted(stems.items(), key=lambda item: (
                    min(value['ts'] for value in item[1]), item[0]))
                for number, (_, items) in enumerate(ordered, 1):
                    for row in items:
                        row['output_name'] = f'{safe(self.rename_base.get())}_{number:04d}{row["p"].suffix.lower()}'

        executor = ResumableOrganizer(out)
        try:
            def progress(number, total, counts, name):
                self.update(
                    number, total,
                    f'整理 {number}/{total}：{name}；新完成 {counts["completed"]}，'
                    f'已整理跳过 {counts["skipped"]}，失败 {counts["failed"]}'
                )

            counts, report_rows = executor.execute(
                self.rows,
                copy_mode=bool(self.copy_mode.get()),
                stop_event=self.stop,
                progress=progress,
            )
            report = write_report(out, report_rows)
        finally:
            executor.close()

        stopped = self.stop.is_set()
        self.update(
            counts['completed'] + counts['skipped'], len(self.rows),
            f'{"已安全停止" if stopped else "整理完成"}：'
            f'新完成 {counts["completed"]}，已整理跳过 {counts["skipped"]}，'
            f'失败 {counts["failed"]}，未整理 {counts["failed"] + counts["pending"]}；{report}'
        )
        elapsed = time.monotonic() - run_started
        summary = (f'整理已完成\n\n新完成：{counts["completed"]} 项\n'
                   f'已整理跳过：{counts["skipped"]} 项\n失败：{counts["failed"]} 项\n'
                   f'未整理：{counts["failed"] + counts["pending"]} 项\n'
                   f'用时：{elapsed / 60:.1f} 分钟\n\n整理记录：{report}')
        self.after(0, lambda text=summary: messagebox.showinfo('执行整理', text, parent=self))

    def start_run(self):
        if not self.rows:
            return messagebox.showwarning('提示', '请先扫描')
        out = Path(self.out.get())
        out.mkdir(parents=True, exist_ok=True)
        executor = ResumableOrganizer(out)
        try:
            required, recognized = executor.estimate_remaining(self.rows)
        finally:
            executor.close()
        if self.copy_mode.get() and shutil.disk_usage(out).free < required:
            return messagebox.showerror('空间不足', '目标磁盘空间不足')
        pending = max(0, len(self.rows) - recognized)
        text = (
            f'目标：{out}\n'
            f'方式：{"复制并保留原文件" if self.copy_mode.get() else "移动原文件（有风险）"}\n'
            f'全部：{len(self.rows)} 项\n已整理可跳过：{recognized} 项\n'
            f'待处理：{pending} 项，预计新增：{required / 1048576:.1f} MB'
        )
        if messagebox.askyesno('确认整理', text):
            self.stop.clear()
            threading.Thread(target=self.full_run, args=(out,), daemon=True).start()


if __name__ == '__main__':
    SafeDragV53MediaOrganizerApp().mainloop()
