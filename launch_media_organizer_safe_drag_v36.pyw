import builtins
import json
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from v3_ui_components import (COLORS, CanvasButton, PathList, RoundedCard,
                              SegmentedControl, ToggleSwitch, Tooltip,
                              rounded_rectangle)
from svg_icon_system import SvgIcon, draw_svg_icon
from folder_tree_panel import FolderTreePanel

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scene-runtime'))
builtins.__file__ = str(ROOT / 'launch_scene_folder_final.pyw')
launcher = ROOT / 'launch_media_organizer_safe_drag_v32.pyw'
source = launcher.read_text(encoding='utf-8').rsplit(
    'SafeDragV32MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV32MediaOrganizerApp = scope['SafeDragV32MediaOrganizerApp']


class ProgressBar(tk.Canvas):
    def __init__(self, master, variable, **kwargs):
        self.variable = variable
        super().__init__(master, height=12, background=master.cget('background'),
                         highlightthickness=0, **kwargs)
        self.bind('<Configure>', self.draw)
        variable.trace_add('write', lambda *_: self.draw())

    def draw(self, _event=None):
        self.delete('all')
        w, h = max(2, self.winfo_width()), max(2, self.winfo_height())
        rounded_rectangle(self, 0, 1, w, h - 1, 6, fill='#DCE3F0', outline='')
        value = max(0, min(100, float(self.variable.get() or 0)))
        done = max(0, w * value / 100)
        if done:
            rounded_rectangle(self, 0, 1, done, h - 1, 6,
                              fill=COLORS['success'] if value >= 100 else COLORS['sidebar'], outline='')
            if done > 12 and value < 100:
                self.create_rectangle(max(0, done - 6), 1, done, h - 1,
                                      fill=COLORS['coral'], outline='')


class SafeDragV36MediaOrganizerApp(SafeDragV32MediaOrganizerApp):
    """V3 presentation layer. Scanning, recognition and organizing stay in V32."""
    UI_SETTINGS = ROOT / 'media_organizer_v3_ui.json'

    def __init__(self):
        super().__init__()
        self.tk.call('tk', 'scaling', 1.0)
        self.title('Media Organizer')
        self.minsize(1280, 760)
        self.configure(background=COLORS['app_bg'])
        self.option_add('*Font', ('Segoe UI', 10))
        self.faces_on.set(False)
        self.scene_on.set(False)
        self.scan_pause = threading.Event()
        self.scan_started_at = None
        self.v3_progress_value = tk.DoubleVar(value=0)
        self.v3_progress_text = tk.StringVar(value='0 / 0')
        self.v3_percent_text = tk.StringVar(value='0%')
        self.v3_phase = tk.StringVar(value='等待扫描')
        self.v3_task = tk.StringVar(value='添加素材并设置整理规则后开始扫描')
        self.v3_eta = tk.StringVar(value='')
        self.v3_state = tk.StringVar(value='准备就绪')
        self._build_theme()
        self._build_shell()
        self._build_setup_v3()
        self._decorate_recognition_v3()
        self._rebuild_recognition_v3()
        self._install_traces()
        self._refresh_path_lists()
        self._refresh_scan_availability()
        self.after_idle(self._responsive_layout)

    def _build_theme(self):
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('V3.TNotebook', background=COLORS['app_bg'], borderwidth=0)
        style.layout('V3.TNotebook.Tab', [])
        style.configure('V3.Treeview', background='white', fieldbackground='white',
                        foreground=COLORS['text'], rowheight=58, borderwidth=0)
        style.map('V3.Treeview', background=[('selected', '#E9EEFF')],
                  foreground=[('selected', COLORS['text'])])
        style.configure('V3.Treeview.Heading', background='#F7F8FB',
                        foreground=COLORS['muted'], relief='flat', padding=(8, 9),
                        font=('Segoe UI Semibold', 9))
        style.configure('V3.TCombobox', padding=(8, 7))

    def _build_shell(self):
        for child in self.winfo_children():
            try:
                child.pack_forget()
                child.grid_forget()
                child.place_forget()
            except tk.TclError:
                pass
        self.shell = self
        self.sidebar_v3 = tk.Frame(self, background=COLORS['sidebar'], width=220)
        self.sidebar_v3.pack(side='left', fill='y')
        self.sidebar_v3.pack_propagate(False)
        self.book.configure(style='V3.TNotebook')
        self.book.pack(side='left', fill='both', expand=True)
        self.content_v3 = self.book
        expanded = True
        try:
            expanded = json.loads(self.UI_SETTINGS.read_text(encoding='utf-8')).get('sidebar_expanded', True)
        except Exception:
            pass
        self.sidebar_expanded = bool(expanded)
        self.logo = tk.Frame(self.sidebar_v3, bg=COLORS['sidebar'])
        self.logo.pack(fill='x', padx=18, pady=(24, 26))
        SvgIcon(self.logo, 'folder', 'white', COLORS['sidebar'], size=38, icon_size=24).pack(side='left')
        self.logo_text = tk.Label(self.logo, text='Media Organizer', bg=COLORS['sidebar'], fg='white', font=('Segoe UI Semibold', 13))
        self.logo_text.pack(side='left', padx=8)
        self.nav_add = CanvasButton(self.sidebar_v3, '添加素材', icon='add', variant='nav-active',
                                    width=188, height=54, command=lambda: self._select_page(0))
        self.nav_add.pack(padx=16, pady=4)
        self.nav_review = CanvasButton(self.sidebar_v3, '识别整理', icon='organize', variant='nav',
                                       width=188, height=54, command=lambda: self._select_page(1))
        self.nav_review.pack(padx=16, pady=4)
        self.recognition_settings_button = CanvasButton(self.sidebar_v3, '识别设置', icon='settings', variant='nav',
                                                         width=188, height=46,
                                                         command=self.toggle_settings_drawer)
        self.recognition_settings_button.pack(padx=16, pady=(2, 4))
        Tooltip(self.recognition_settings_button, '识别设置')
        self.settings_drawer = None
        self.collapse_button = CanvasButton(self.sidebar_v3, '', icon='chevron-left', variant='nav-active',
                                            width=40, height=40, command=self._toggle_sidebar)
        self.collapse_button.place(relx=1, x=-20, y=16, anchor='n')
        if not self.sidebar_expanded:
            self._apply_sidebar(False)

    def toggle_settings_drawer(self):
        if self.settings_drawer is not None and self.settings_drawer.winfo_exists():
            self.close_settings_drawer(); return
        drawer = tk.Toplevel(self); self.settings_drawer = drawer
        drawer.overrideredirect(True); drawer.transient(self); drawer.configure(bg=COLORS['border'])
        width = 350; x = self.sidebar_v3.winfo_rootx() + self.sidebar_v3.winfo_width(); y = self.winfo_rooty() + 48
        height = max(620, self.winfo_height() - 80); drawer.geometry(f'{width}x{height}+{x}+{y}')
        surface = tk.Frame(drawer, bg='white'); surface.pack(fill='both', expand=True, padx=1, pady=1)
        head = tk.Frame(surface, bg='white'); head.pack(fill='x', padx=20, pady=(18, 10))
        tk.Label(head, text='识别设置', bg='white', fg='#17213C', font=('Segoe UI Semibold', 16)).pack(side='left')
        CanvasButton(head, '', icon='close', width=36, height=36, command=self.close_settings_drawer).pack(side='right')
        tk.Label(surface, text='设置识别、命名、视频分析与文件安全选项', bg='white', fg=COLORS['muted'], font=('Segoe UI', 9)).pack(anchor='w', padx=20, pady=(0, 12))
        def group(title):
            tk.Label(surface, text=title, bg='white', fg=COLORS['muted'], font=('Segoe UI Semibold', 8)).pack(anchor='w', padx=20, pady=(12, 5))
        def option(text, variable, hint=''):
            row = tk.Frame(surface, bg='white'); row.pack(fill='x', padx=20, pady=6)
            ToggleSwitch(row, variable, command=self._drawer_setting_changed).pack(side='right')
            labels = tk.Frame(row, bg='white'); labels.pack(side='left', fill='x', expand=True)
            tk.Label(labels, text=text, bg='white', fg=COLORS['text'], anchor='w', font=('Segoe UI', 9)).pack(fill='x')
            if hint: tk.Label(labels, text=hint, bg='white', fg=COLORS['muted'], anchor='w', font=('Segoe UI', 7)).pack(fill='x')
        group('识别')
        option('场景识别并分类', self.scene_on)
        option('模特识别并分类', self.faces_on)
        option('画质、重复、连拍识别', self.smart)
        if hasattr(self, 'open_people_manager'):
            CanvasButton(surface, '模特分类管理', width=150, height=36, command=self.open_people_manager).pack(anchor='w', padx=20, pady=(2, 6))
        group('视频分析')
        option('视频镜头、关键帧、画质分析', self.video_on)
        group('文件安全')
        option('复制并保留原文件', self.copy_mode, '推荐开启，不修改或删除源文件')
        tk.Label(surface, text='扫描进行中修改设置时，修改后的设置将在下次扫描时生效。', wraplength=300,
                 bg='#FFF7E8', fg='#8A5B16', padx=10, pady=8, font=('Segoe UI', 8)).pack(fill='x', padx=20, pady=(18, 0))
        drawer.bind('<Escape>', lambda _e: self.close_settings_drawer());drawer.update_idletasks();drawer.lift();drawer.attributes('-topmost',True);drawer.after(300,lambda:drawer.winfo_exists() and drawer.attributes('-topmost',False))
        self.after(180, self._bind_drawer_outside_click)

    def _bind_drawer_outside_click(self):
        if self.settings_drawer is None or not self.settings_drawer.winfo_exists(): return
        if getattr(self, '_drawer_click_binding', None):
            try: self.unbind('<Button-1>', self._drawer_click_binding)
            except tk.TclError: pass
        self._drawer_click_binding = self.bind('<Button-1>', self._drawer_outside_click, add='+')

    def _drawer_outside_click(self, event):
        drawer=self.settings_drawer
        if drawer is None or not drawer.winfo_exists(): return
        x,y=event.x_root,event.y_root;dx,dy=drawer.winfo_rootx(),drawer.winfo_rooty();dw,dh=drawer.winfo_width(),drawer.winfo_height()
        bx,by=self.recognition_settings_button.winfo_rootx(),self.recognition_settings_button.winfo_rooty();bw,bh=self.recognition_settings_button.winfo_width(),self.recognition_settings_button.winfo_height()
        if not (dx<=x<=dx+dw and dy<=y<=dy+dh) and not (bx<=x<=bx+bw and by<=y<=by+bh): self.close_settings_drawer()
    def _drawer_setting_changed(self):
        if getattr(self, 'scan_busy', False):
            self.status.set('修改后的设置将在下次扫描时生效')
            messagebox.showinfo('设置已记录', '修改后的设置将在下次扫描时生效', parent=self)

    def _close_drawer_if_unfocused(self):
        if self.settings_drawer is not None and self.settings_drawer.winfo_exists():
            try:
                focused = self.focus_get()
                if focused is None or focused.winfo_toplevel() is not self.settings_drawer: self.close_settings_drawer()
            except tk.TclError: self.close_settings_drawer()

    def close_settings_drawer(self):
        if self.settings_drawer is not None:
            try: self.settings_drawer.destroy()
            except tk.TclError: pass
        self.settings_drawer = None
    def _select_page(self, index):
        self.book.select(index)
        self.nav_add.configure(variant='nav-active' if index == 0 else 'nav')
        self.nav_review.configure(variant='nav-active' if index == 1 else 'nav')

    def _toggle_sidebar(self):
        self._apply_sidebar(not self.sidebar_expanded)
        try:
            data=json.loads(self.UI_SETTINGS.read_text(encoding='utf-8')) if self.UI_SETTINGS.exists() else {};data['sidebar_expanded']=self.sidebar_expanded;self.UI_SETTINGS.write_text(json.dumps(data,ensure_ascii=False,indent=2), encoding='utf-8')
        except OSError:
            pass

    def _apply_sidebar(self, expanded):
        self.sidebar_expanded = expanded
        width = 220 if expanded else 72
        self.sidebar_v3.configure(width=width)
        self.logo_text.configure(text='Media Organizer' if expanded else '')
        self.nav_add.configure(text='添加素材' if expanded else '', width=188 if expanded else 48)
        self.nav_review.configure(text='识别整理' if expanded else '', width=188 if expanded else 48)
        self.recognition_settings_button.configure(text='识别设置' if expanded else '', width=188 if expanded else 48)
        self.collapse_button.configure(icon='chevron-left' if expanded else 'chevron-right')

    def _page_header(self, parent, title, subtitle):
        head = tk.Frame(parent, bg=COLORS['app_bg'])
        head.pack(fill='x', pady=(0, 16))
        tk.Label(head, text=title, bg=COLORS['app_bg'], fg='#17213C',
                 font=('Segoe UI Semibold', 24)).pack(anchor='w')
        tk.Label(head, text=subtitle, bg=COLORS['app_bg'], fg=COLORS['muted'],
                 font=('Segoe UI', 10)).pack(anchor='w', pady=(3, 0))
        return head

    def _build_setup_v3(self):
        for child in self.setup.winfo_children():
            child.destroy()
        self.setup.configure(style='V3.TNotebook')
        page = tk.Frame(self.setup, bg=COLORS['app_bg'])
        page.pack(fill='both', expand=True, padx=28, pady=22)
        self._page_header(page, '添加素材', '添加素材来源，并设置整理规则')
        body = tk.Frame(page, bg=COLORS['app_bg'])
        body.pack(fill='both', expand=True)
        self.setup_cards = body
        self.source_card = RoundedCard(body, height=560)
        self.rule_card = RoundedCard(body, height=560)
        self._build_source_card(self.source_card.body)
        self._build_rule_card(self.rule_card.body)
        footer = RoundedCard(page, height=78, padding=14)
        footer.pack(fill='x', pady=(16, 0))
        tk.Label(footer.body, text='●  默认复制并保留原文件，不会修改源文件', bg='white',
                 fg=COLORS['muted'], font=('Segoe UI', 9)).pack(side='left', padx=8)
        self.save_draft_button = CanvasButton(footer.body, '保存草稿', width=140,
                                              command=self._save_draft)
        self.save_draft_button.pack(side='right', padx=(10, 0))
        self.scan_button = CanvasButton(footer.body, '开始扫描', variant='primary', width=150,
                                        command=self.start_scan)
        self.scan_button.pack(side='right')
        self.src_box = tk.Listbox(self.setup)
        self.exc_box = tk.Listbox(self.setup)
        self.bind('<Configure>', lambda _e: self.after_idle(self._responsive_layout), add='+')

    def _card_title(self, parent, icon, title, aside=''):
        row = tk.Frame(parent, bg='white')
        row.pack(fill='x', pady=(0, 14))
        SvgIcon(row, icon, COLORS['sidebar'], 'white', size=32, icon_size=22).pack(side='left')
        tk.Label(row, text=title, bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 14)).pack(side='left', padx=10)
        if aside:
            tk.Label(row, text=aside, bg='white', fg=COLORS['muted'],
                     font=('Segoe UI', 9)).pack(side='right')

    def _build_source_card(self, parent):
        self._card_title(parent, 'folder', '素材来源', '可拖入多个文件夹')
        drop = tk.Canvas(parent, height=230, bg='white', highlightthickness=0, cursor='hand2')
        drop.pack(fill='x')
        def draw(_e=None):
            drop.delete('all'); w = drop.winfo_width()
            drop.create_rectangle(2, 2, w-2, 228, fill='#FBFCFE', outline='#BFCBE3', dash=(5, 4))
            rounded_rectangle(drop, w/2-30, 32, w/2+30, 92, 12, fill='#EEF2FF', outline='')
            draw_svg_icon(drop, 'folder-upload', w/2, 62, 30, COLORS['blue'], 2)
            drop.create_text(w/2, 112, text='拖入文件夹，或点击选择', fill='#17213C', font=('Segoe UI Semibold', 13))
            drop.create_text(w/2, 140, text='支持添加多个文件夹', fill=COLORS['muted'], font=('Segoe UI', 9))
            drop.create_window(w/2, 190, window=choose, tags='choose')
        drop.bind('<Configure>', draw); drop.bind('<ButtonRelease-1>', lambda _e: self.add_source())
        choose = CanvasButton(parent, '选择文件夹', icon='add', variant='primary', width=200,
                              command=self.add_source)
        def place_button(_e=None): drop.coords('choose', drop.winfo_width()/2, 190)
        drop.bind('<Configure>', lambda e: (draw(e), place_button(e)))
        try:
            drop.drop_target_register('DND_Files'); drop.dnd_bind('<<Drop>>', self.drop_src)
        except Exception:
            pass
        count = tk.Frame(parent, bg='white'); count.pack(fill='x', pady=(18, 5))
        self.source_count_label = tk.Label(count, text='', bg='white', fg='#17213C',
                                           font=('Segoe UI Semibold', 10))
        self.source_count_label.pack(side='left')
        self.source_list_v3 = PathList(parent, lambda: self.sources, self._remove_source_index,
                                       empty_text='尚未添加素材来源')
        self.source_list_v3.pack(fill='both', expand=True)

    def _section(self, parent, title, hint=''):
        row = tk.Frame(parent, bg='white'); row.pack(fill='x', pady=(0, 7))
        tk.Label(row, text=title, bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 10)).pack(side='left')
        if hint:
            tk.Label(row, text=hint, bg='white', fg=COLORS['muted'],
                     font=('Segoe UI', 8)).pack(side='right')
        return row

    def _separator(self, parent):
        tk.Frame(parent, bg=COLORS['border'], height=1).pack(fill='x', pady=11)

    def _build_rule_card(self, parent):
        self._card_title(parent, 'settings', '整理规则')
        self._section(parent, '排除目录', '不参与整理的目录')
        CanvasButton(parent, '添加排除目录', icon='add', width=300, height=42,
                     command=self.add_exclusion).pack(fill='x')
        self.exclude_list_v3 = PathList(parent, lambda: self.excludes, self._remove_exclude_index,
                                        empty_text='暂无排除目录')
        self.exclude_list_v3.pack(fill='x', pady=(5, 0))
        self._separator(parent)
        self._section(parent, '目录命名')
        SegmentedControl(parent, self.english,
                         [('中文目录', False), ('English folders', True)],
                         command=self.retarget).pack(anchor='w')
        self._separator(parent)
        self._section(parent, '分类目录（可选）', '默认不勾选，可单独或同时启用')
        for text, variable in [('模特识别并分类', self.faces_on), ('场景识别并分类', self.scene_on)]:
            row = tk.Frame(parent, bg='white'); row.pack(fill='x', pady=4)
            ToggleSwitch(row, variable, command=self._refresh_scan_availability).pack(side='left')
            tk.Label(row, text=text, bg='white', fg=COLORS['text']).pack(side='left', padx=10)
        self._separator(parent)
        self._section(parent, '整理后的保存位置')
        outrow = tk.Frame(parent, bg='white'); outrow.pack(fill='x')
        self.output_entry_v3 = tk.Entry(outrow, textvariable=self.out, relief='flat', bd=0,
                                        highlightthickness=1, highlightbackground=COLORS['border'],
                                        highlightcolor=COLORS['blue'], font=('Segoe UI', 10))
        self.output_entry_v3.pack(side='left', fill='x', expand=True, ipady=10)
        CanvasButton(outrow, '浏览…', width=105, command=self.output).pack(side='left', padx=(8, 0))
        self.validation_label = tk.Label(parent, text='', bg='white', fg=COLORS['warning'],
                                         font=('Segoe UI', 8), anchor='w')
        self.validation_label.pack(fill='x', pady=(5, 0))

    def _decorate_recognition_v3(self):
        self.preview.configure(style='V3.TNotebook')
        old_children = list(self.preview.winfo_children())
        first_packed = next((child for child in old_children if child.winfo_manager() == 'pack'), None)
        header = tk.Frame(self.preview, bg=COLORS['app_bg'])
        header.pack(fill='x', padx=26, pady=(20, 8), before=first_packed)
        row = self._page_header(header, '识别与整理', '扫描、识别并分类您的媒体素材')
        self.rescan_button = CanvasButton(row, '重新扫描', width=120, command=self.start_scan)
        self.rescan_button.pack(side='right')
        self.progress_card_v3 = RoundedCard(self.preview, height=154, padding=16)
        self.progress_card_v3.pack(fill='x', padx=26, pady=(0, 12), before=first_packed)
        top = tk.Frame(self.progress_card_v3.body, bg='white'); top.pack(fill='x')
        tk.Label(top, textvariable=self.v3_state, bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 13)).pack(side='left')
        self.state_badge = tk.Label(top, text='准备就绪', bg=COLORS['soft_blue'], fg=COLORS['blue'],
                                    padx=10, pady=4, font=('Segoe UI Semibold', 8))
        self.state_badge.pack(side='left', padx=10)
        self.pause_button = CanvasButton(top, '暂停扫描', width=110, height=36,
                                         command=self.toggle_pause)
        self.pause_button.pack(side='right')
        info = tk.Frame(self.progress_card_v3.body, bg='white'); info.pack(fill='x', pady=(10, 5))
        tk.Label(info, textvariable=self.v3_phase, bg='white', fg=COLORS['muted']).pack(side='left')
        tk.Label(info, textvariable=self.v3_percent_text, bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 10)).pack(side='right')
        tk.Label(info, textvariable=self.v3_progress_text, bg='white', fg=COLORS['muted']).pack(side='right', padx=12)
        ProgressBar(self.progress_card_v3.body, self.v3_progress_value).pack(fill='x')
        bottom = tk.Frame(self.progress_card_v3.body, bg='white'); bottom.pack(fill='x', pady=(7, 0))
        tk.Label(bottom, textvariable=self.v3_task, bg='white', fg=COLORS['muted'], font=('Segoe UI', 8)).pack(side='left')
        tk.Label(bottom, textvariable=self.v3_eta, bg='white', fg=COLORS['muted'], font=('Segoe UI', 8)).pack(side='right')
        self.pause_button.configure(state='disabled')
        try:
            self.tree.configure(style='V3.Treeview')
        except tk.TclError:
            pass

    def _rebuild_recognition_v3(self):
        """Replace every visible legacy recognition control with the V3 composition."""
        legacy_buttons = {}
        for widget in self._descendants(self.preview):
            if widget.winfo_class() == 'TButton':
                try:
                    legacy_buttons[str(widget.cget('text'))] = widget
                except tk.TclError:
                    pass
        legacy_sidebar = self.sidebar_list.master.master
        old_tree = self.tree
        old_scroll = next((w for w in self.preview.winfo_children()
                           if w.winfo_class() == 'TScrollbar'), None)
        for child in self.preview.winfo_children():
            try:
                child.pack_forget(); child.grid_forget(); child.place_forget()
            except tk.TclError:
                pass

        root = tk.Frame(self.preview, bg=COLORS['app_bg'])
        root.pack(fill='both', expand=True, padx=22, pady=16)
        head = tk.Frame(root, bg=COLORS['app_bg']); head.pack(fill='x', pady=(0, 10))
        titles = tk.Frame(head, bg=COLORS['app_bg']); titles.pack(side='left')
        tk.Label(titles, text='识别与整理', bg=COLORS['app_bg'], fg='#17213C',
                 font=('Segoe UI Semibold', 23)).pack(anchor='w')
        tk.Label(titles, text='扫描、识别并分类您的媒体素材', bg=COLORS['app_bg'],
                 fg=COLORS['muted'], font=('Segoe UI', 10)).pack(anchor='w', pady=(2, 0))
        self.return_selection_button = CanvasButton(head, '返回选择', icon='chevron-left', width=112,
                                                     command=lambda: self._select_page(0))
        self.return_selection_button.pack(side='right', pady=6)
        self.rescan_button = CanvasButton(head, '扫描并预览', icon='scan', width=132,
                                          command=self.start_scan)
        self.rescan_button.pack(side='right', padx=(0, 8), pady=6)

        self.progress_card_v3 = RoundedCard(root, height=126, padding=14)
        self.progress_card_v3.pack(fill='x', pady=(0, 10))
        pc = self.progress_card_v3.body
        top = tk.Frame(pc, bg='white'); top.pack(fill='x')
        SvgIcon(top, 'scan', COLORS['blue'], '#EEF2FF', size=54).pack(side='left', padx=(0, 12))
        textcol = tk.Frame(top, bg='white'); textcol.pack(side='left', fill='x', expand=True)
        titleline = tk.Frame(textcol, bg='white'); titleline.pack(fill='x')
        tk.Label(titleline, textvariable=self.v3_state, bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 12)).pack(side='left')
        self.state_badge = tk.Label(titleline, text='准备就绪', bg=COLORS['soft_blue'],
                                    fg=COLORS['blue'], padx=10, pady=3,
                                    font=('Segoe UI Semibold', 8))
        self.state_badge.pack(side='left', padx=10)
        self.stop_scan_button = CanvasButton(top, '停止扫描', icon='stop', variant='danger', width=112, height=38,
                                             command=self.stop_scan)
        self.stop_scan_button.pack(side='right', padx=(8, 0))
        self.pause_button = CanvasButton(top, '暂停扫描', icon='pause', width=124, height=38,
                                         command=self.toggle_pause)
        self.pause_button.pack(side='right', padx=(12, 0))
        phase = tk.Frame(textcol, bg='white'); phase.pack(fill='x', pady=(5, 4))
        tk.Label(phase, text='当前阶段：', bg='white', fg=COLORS['muted'],
                 font=('Segoe UI', 9)).pack(side='left')
        tk.Label(phase, textvariable=self.v3_phase, bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 9)).pack(side='left')
        tk.Label(phase, textvariable=self.v3_progress_text, bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 9)).pack(side='left', padx=15)
        tk.Label(phase, textvariable=self.v3_percent_text, bg='white', fg='#17213C',
                 font=('Segoe UI Semibold', 9)).pack(side='left')
        tk.Label(phase, textvariable=self.v3_eta, bg='white', fg=COLORS['muted'],
                 font=('Segoe UI', 9)).pack(side='right')
        ProgressBar(textcol, self.v3_progress_value).pack(fill='x')
        tk.Label(textcol, textvariable=self.v3_task, bg='white', fg=COLORS['muted'],
                 font=('Segoe UI', 8)).pack(anchor='w', pady=(4, 0))
        self.pause_button.configure(state='disabled')
        self.stop_scan_button.configure(state='disabled')

        stats = tk.Frame(root, bg=COLORS['app_bg']); stats.pack(fill='x', pady=(0, 10))
        for stat_column in range(4):
            stats.grid_columnconfigure(stat_column, weight=1, uniform='material-stat')
        stat_names = ('全部素材', '照片', '视频', '文件异常')
        stat_icons = ('folder', 'photo', 'video', 'warning')
        stat_colors = (COLORS['blue'], '#159CC4', '#6C4DE6', COLORS['coral'])
        self.v3_stat_values = []
        for index, (name, icon, color) in enumerate(zip(stat_names, stat_icons, stat_colors)):
            card = RoundedCard(stats, height=82, padding=10)
            card.grid(row=0, column=index, sticky='nsew', padx=5)
            row = tk.Frame(card.body, bg='white', cursor='hand2'); row.pack(fill='both', expand=True)
            tile = ('#EEF2FF', '#EAF8FC', '#F1EDFF', '#FFF0EE')[index]
            SvgIcon(row, icon, color, tile, size=48).pack(side='left', padx=(0, 10))
            labels = tk.Frame(row, bg='white'); labels.pack(side='left', fill='both', expand=True)
            tk.Label(labels, text=name, bg='white', fg=COLORS['muted'],
                     font=('Segoe UI', 9)).pack(anchor='w')
            value = tk.StringVar(value='0'); self.v3_stat_values.append(value)
            tk.Label(labels, textvariable=value, bg='white', fg='#17213C',
                     font=('Segoe UI Semibold', 17)).pack(anchor='w')
            SvgIcon(row, 'chevron-right', '#17213C', 'white', size=34, icon_size=16).pack(side='right', padx=4)
            category = ('全部', '照片', '视频', '文件异常')[index]
            for target in (card, card.body, row, labels):
                target.bind('<ButtonRelease-1>', lambda _e, c=category: self.open_category(c), add='+')

        stats.pack_forget()

        content = tk.Frame(root, bg=COLORS['app_bg']); content.pack(fill='both', expand=True)
        left = tk.Frame(content, bg=COLORS['app_bg'], width=390); left.pack(side='left', fill='y', padx=(0, 10)); left.pack_propagate(False)
        right = RoundedCard(content, padding=12); right.pack(side='left', fill='both', expand=True)
        folders = RoundedCard(left, padding=12); folders.pack(fill='both', expand=True)
        legacy_sidebar.pack_forget()
        self.folder_tree_panel = FolderTreePanel(folders.body, self)
        self.folder_tree_panel.pack(fill='both', expand=True)

        settings = RoundedCard(left, height=300, padding=12); settings.pack(fill='both', expand=True)
        sh = tk.Frame(settings.body, bg='white'); sh.pack(fill='x', pady=(0, 8))
        tk.Label(sh, text='⚙  识别设置', bg='white', fg='#17213C', font=('Segoe UI Semibold', 11)).pack(side='left')
        for text, var, hint in (
            ('场景识别并分类', self.scene_on, '照片直接识别，视频通过关键帧识别'),
            ('模特识别并分类', self.faces_on, ''),
            ('画质/重复/连拍识别', self.smart, ''),
            ('复制并保留原文件（推荐）', self.copy_mode, '')):
            row = tk.Frame(settings.body, bg='white'); row.pack(fill='x', pady=5)
            ToggleSwitch(row, var).pack(side='left')
            labelcol = tk.Frame(row, bg='white'); labelcol.pack(side='left', padx=8, fill='x', expand=True)
            tk.Label(labelcol, text=text, bg='white', fg=COLORS['text'], anchor='w', font=('Segoe UI', 9)).pack(fill='x')
            if hint: tk.Label(labelcol, text=hint, bg='white', fg=COLORS['muted'], anchor='w', font=('Segoe UI', 7)).pack(fill='x')
        manager = legacy_buttons.get('模特分类管理')
        if manager:
            CanvasButton(settings.body, '模特分类管理', width=150, height=34,
                         command=manager.invoke).pack(anchor='e', pady=(4, 0))

        rb = right.body
        output_bar = tk.Frame(rb, bg='#F7F9FC', highlightthickness=1, highlightbackground=COLORS['border'])
        output_bar.pack(fill='x', pady=(0, 8))
        tk.Label(output_bar, text='保存位置：', bg='#F7F9FC', fg=COLORS['muted'], font=('Segoe UI', 8)).pack(side='left', padx=(10, 2), pady=7)
        tk.Label(output_bar, textvariable=self.out, bg='#F7F9FC', fg=COLORS['text'], font=('Segoe UI', 8), anchor='w').pack(side='left', fill='x', expand=True)
        self.output_change_button = CanvasButton(output_bar, '更改位置', width=90, height=30, command=self._change_output_guarded)
        self.output_change_button.pack(side='right', padx=6, pady=4)
        toolbar = tk.Frame(rb, bg='white'); toolbar.pack(fill='x', pady=(0, 10))
        toolbar_main = tk.Frame(toolbar, bg='white'); toolbar_main.pack(fill='x')
        toolbar_actions = tk.Frame(toolbar, bg='white'); toolbar_actions.pack(fill='x', pady=(6, 0))
        self.filter_button_text = tk.StringVar(value='全部类型')
        self.filter_button_v3 = CanvasButton(toolbar_main, '全部类型', icon='filter', width=118, height=40, command=self._show_filter_menu)
        self.filter_button_v3.pack(side='left', padx=(0, 8))

        batch = legacy_buttons.get('批量调整')
        export = legacy_buttons.get('导出审核报告')
        run = legacy_buttons.get('执行整理')
        CanvasButton(toolbar_main, '批量调整', icon='batch', width=112, height=38, command=self._open_batch_adjustment).pack(side='left', padx=4)
        if export: CanvasButton(toolbar_main, '导出审核报告', icon='export', width=130, height=38, command=export.invoke).pack(side='left', padx=4)
        CanvasButton(toolbar_main, '列设置', icon='columns', width=86, height=38, command=self._show_column_settings).pack(side='left', padx=4)
        self.keyframes_button_v3 = CanvasButton(toolbar_actions, '视频关键帧', icon='video', width=112, height=38, command=self.open_keyframes)
        self.keyframes_button_v3.pack(side='left', padx=4)
        self.open_original_button_v3 = CanvasButton(toolbar_actions, '打开原文件', icon='open', width=112, height=38, command=self.open_original)
        self.open_original_button_v3.pack(side='left', padx=4)
        self.remove_plan_button_v3 = CanvasButton(toolbar_actions, '从整理中删除', icon='delete', variant='danger', width=128, height=38, command=self.remove_selected_from_plan)
        self.remove_plan_button_v3.pack(side='left', padx=4)
        self._execute_legacy = run
        self.execute_button_v3 = CanvasButton(toolbar_actions, '扫描并预览' if not self.rows else '执行整理', variant='primary', width=122, height=38,
                                               command=self.start_scan if not self.rows else (run.invoke if run else lambda: None))
        self.execute_button_v3.pack(side='right', padx=(4, 0))
        table = tk.Frame(rb, bg='white'); table.pack(fill='both', expand=True)
        old_tree.pack_forget(); old_tree.place_forget()
        new_tree = ttk.Treeview(table, columns=tuple(old_tree['columns']), show='tree headings',
                                selectmode='extended', style='V3.Treeview')
        new_tree.configure(displaycolumns=tuple(old_tree['displaycolumns']))
        for column in ('#0',) + tuple(old_tree['columns']):
            heading = old_tree.heading(column)
            new_tree.heading(column, text=heading.get('text', ''), anchor='center')
            config = old_tree.column(column)
            new_tree.column(column, width=config.get('width', 100), minwidth=config.get('minwidth', 20),
                            stretch=config.get('stretch', False), anchor='center')
        for sequence in self.tk.splitlist(old_tree.bind()):
            script = old_tree.bind(sequence)
            if script: new_tree.bind(sequence, script, add='+')
        new_scroll = ttk.Scrollbar(table, orient='vertical', command=new_tree.yview)
        hscroll = ttk.Scrollbar(rb, orient='horizontal', command=new_tree.xview)
        new_tree.configure(yscrollcommand=new_scroll.set, xscrollcommand=hscroll.set)
        new_tree.pack(side='left', fill='both', expand=True)
        new_scroll.pack(side='right', fill='y')
        self.table_hscroll = hscroll
        self.tree = new_tree
        try:
            from tree_thumbnail_column import TreeThumbnailColumn
            self.tree_thumbnails = TreeThumbnailColumn(self)
        except Exception:
            pass
        foot = tk.Frame(rb, bg='white'); foot.pack(fill='x', pady=(8, 0))
        self.v3_selection_text = tk.StringVar(value='已选择 0 个素材')
        tk.Label(foot, textvariable=self.v3_selection_text, bg='white', fg=COLORS['muted'], font=('Segoe UI', 8)).pack(side='left')
        self.v3_total_text = tk.StringVar(value='共 0 条')
        tk.Label(foot, textvariable=self.v3_total_text, bg='white', fg=COLORS['muted'], font=('Segoe UI', 8)).pack(side='right')
        new_tree.bind('<<TreeviewSelect>>', self._v3_selection_changed, add='+')
        self._v3_selection_changed()
        settings.pack_forget()
        folders.pack_configure(fill='both', expand=True)
        self.v3_recognition_root = root
        self._sync_v3_counts()
        self._apply_column_visibility()
        self.refresh_sidebar()

    def _popup_actions(self, actions, anchor=None):
        existing = getattr(self, 'active_popup', None)
        if existing is not None and existing.winfo_exists():
            same_anchor = getattr(self, 'active_popup_anchor', None) is anchor
            self._close_active_popup()
            if same_anchor: return
        popup = tk.Toplevel(self); self.active_popup=popup; self.active_popup_anchor=anchor
        popup.overrideredirect(True); popup.transient(self); popup.configure(bg=COLORS['border'])
        body = tk.Frame(popup, bg='white'); body.pack(fill='both', expand=True, padx=1, pady=1)
        for label, command, enabled in actions:
            button = CanvasButton(body, label, width=190, height=38, command=lambda c=command, p=popup: (p.destroy(), c()))
            button.pack(fill='x', padx=6, pady=3)
            if not enabled: button.configure(state='disabled')
        popup.update_idletasks(); anchor=anchor or self
        x=anchor.winfo_rootx()+anchor.winfo_width()-popup.winfo_reqwidth(); y=anchor.winfo_rooty()+anchor.winfo_height()+6
        screen_w=self.winfo_screenwidth();screen_h=self.winfo_screenheight();x=max(4,min(x,screen_w-popup.winfo_reqwidth()-4))
        if y+popup.winfo_reqheight()>screen_h-8:y=anchor.winfo_rooty()-popup.winfo_reqheight()-6
        popup_w, popup_h = popup.winfo_reqwidth(), popup.winfo_reqheight()
        popup.geometry(f'{popup_w}x{popup_h}+{int(x)}+{int(max(4,y))}')
        popup.update_idletasks(); popup.lift(); popup.attributes('-topmost', True); popup.after(250, lambda: popup.winfo_exists() and popup.attributes('-topmost', False))
        popup.bind('<Escape>', lambda _e: self._close_active_popup())
        self.after(120, self._bind_popup_outside_click)

    def _bind_popup_outside_click(self):
        popup = getattr(self, 'active_popup', None)
        if popup is None or not popup.winfo_exists(): return
        binding = getattr(self, '_popup_click_binding', None)
        if binding:
            try: self.unbind('<Button-1>', binding)
            except tk.TclError: pass
        self._popup_click_binding = self.bind('<Button-1>', self._popup_outside_click, add='+')

    def _popup_outside_click(self, event):
        popup = getattr(self, 'active_popup', None); anchor = getattr(self, 'active_popup_anchor', None)
        if popup is None or not popup.winfo_exists(): return
        x, y = event.x_root, event.y_root
        px, py, pw, ph = popup.winfo_rootx(), popup.winfo_rooty(), popup.winfo_width(), popup.winfo_height()
        inside_popup = px <= x <= px + pw and py <= y <= py + ph
        inside_anchor = False
        if anchor is not None and anchor.winfo_exists():
            ax, ay, aw, ah = anchor.winfo_rootx(), anchor.winfo_rooty(), anchor.winfo_width(), anchor.winfo_height()
            inside_anchor = ax <= x <= ax + aw and ay <= y <= ay + ah
        if not inside_popup and not inside_anchor: self._close_active_popup()

    def _close_active_popup(self):
        popup = getattr(self, 'active_popup', None)
        if popup is not None:
            try: popup.destroy()
            except tk.TclError: pass
        self.active_popup = None; self.active_popup_anchor = None
        binding = getattr(self, '_popup_click_binding', None)
        if binding:
            try: self.unbind('<Button-1>', binding)
            except tk.TclError: pass
            self._popup_click_binding = None
    def _show_top_more_menu(self):
        self._popup_actions([
            ('扫描并预览' if not self.rows else '重新扫描', self.start_scan, not self.scan_busy),
            ('返回选择', lambda: self._select_page(0), True),
        ], self.rescan_button)

    def open_material_folders(self):
        manager = getattr(self, '_modern_folder_manager', None)
        if manager is not None and manager.winfo_exists():
            manager.lift(); manager.focus_force(); return
        from material_folder_manager_modern import ModernMaterialFolderManager
        self._modern_folder_manager = ModernMaterialFolderManager(self)
    def show_folder_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid and iid not in self.tree.selection():
            self.tree.selection_set(iid); self.tree.focus(iid)
        if not iid: return
        actions = [('新建文件夹并放入选中素材…', self.new_folder_for_selection, True, 'secondary')]
        names = self.folder_names()
        if names:
            for name in names[:8]:
                actions.append((f'移入文件夹：{name}', lambda value=name: self.assign_rows(self.selected_rows(), value), True, 'secondary'))
        else:
            actions.append(('暂无可用的自定义文件夹', lambda: None, False, 'secondary'))
        actions.append(('移出自定义文件夹（恢复自动分类）', self.remove_selection_from_folder, True, 'secondary'))
        actions.append((f'从本次整理中删除（{len(self.tree.selection())} 个）', self.remove_selected_from_plan, True, 'danger'))
        self._show_context_actions(actions, event.x_root, event.y_root)

    def _show_context_actions(self, actions, x, y):
        self._close_active_popup()
        popup = tk.Toplevel(self); self.active_popup = popup; self.active_popup_anchor = None
        popup.overrideredirect(True); popup.transient(self); popup.configure(bg=COLORS['border'])
        body = tk.Frame(popup, bg='white'); body.pack(fill='both', expand=True, padx=1, pady=1)
        for label, command, enabled, variant in actions:
            def run(action=command):
                self._close_active_popup(); action()
            button = CanvasButton(body, label, width=300, height=38, variant=variant, command=run)
            button.pack(fill='x', padx=6, pady=3)
            if not enabled: button.configure(state='disabled')
        popup.update_idletasks(); width, height = popup.winfo_reqwidth(), popup.winfo_reqheight()
        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        x = max(4, min(int(x), screen_w - width - 4)); y = max(4, min(int(y), screen_h - height - 4))
        popup.geometry(f'{width}x{height}+{x}+{y}'); popup.update_idletasks(); popup.lift(); popup.attributes('-topmost', True)
        popup.after(250, lambda: popup.winfo_exists() and popup.attributes('-topmost', False))
        popup.bind('<Escape>', lambda _e: self._close_active_popup())
        self.after(120, self._bind_popup_outside_click)
    def _show_table_more_menu(self):
        selected = list(self.tree.selection()); video = False
        if selected:
            try: video = any(self.rows[int(i)].get('kind') == '视频' for i in selected)
            except (ValueError, IndexError): pass
        self._popup_actions([
            ('打开选中视频关键帧', self.open_keyframes, bool(selected) and video and not self.scan_busy),
            ('打开原文件', self.open_original, bool(selected)),
            ('从整理中删除', self.remove_selected_from_plan, bool(selected) and not self.scan_busy),
        ], self.table_more_button)

    def _show_filter_menu(self):
        options = ('全部类型','照片','视频','文件异常','重复素材','连拍素材','低画质素材','待审核','建议保留','建议删除')
        self._popup_actions([(label, lambda v=label: self._select_filter(v), True) for label in options], self.filter_button_v3)

    def _select_filter(self, label):
        self.extra_filter = label
        standard = {'全部类型':'全部','照片':'照片','视频':'视频','文件异常':'文件异常'}
        self.filter_var.set(standard.get(label, '全部')); self.filter_button_v3.configure(text=label); self.apply_filter()

    def match(self, row):
        if getattr(self, 'extra_filter', '全部类型') in ('全部类型','照片','视频','文件异常'):
            return super().match(row)
        text = self.search_var.get().strip().lower()
        haystack = ' '.join([row['p'].name,row.get('dev',''),row.get('place',''),row.get('recommend','')]).lower()
        if text and text not in haystack: return False
        mode = self.extra_filter
        if mode == '重复素材': return bool(row.get('duplicate'))
        if mode == '连拍素材': return bool(row.get('burst'))
        if mode == '低画质素材': return row.get('analysis',{}).get('quality',100) < 45
        if mode == '待审核': return row.get('recommend','') in ('','待审核','未分析')
        if mode == '建议保留': return '保留' in row.get('recommend','')
        if mode == '建议删除': return any(x in row.get('recommend','') for x in ('删除','排除','无法解码'))
        return True

    def _change_output_guarded(self):
        if self.scan_busy:
            return messagebox.showinfo('暂时不能更改', '扫描或整理执行期间不能修改保存位置。', parent=self)
        self.output()

    def _show_column_settings(self):
        columns = [('地点','place'),('设备','device'),('画质','quality'),('重复组','duplicate'),('连拍组','burst'),('处理建议','recommend')]
        popup = tk.Toplevel(self); popup.title('列设置'); popup.transient(self); popup.resizable(False,False); popup.configure(bg=COLORS['app_bg'])
        card=RoundedCard(popup,padding=16);card.pack(fill='both',expand=True,padx=12,pady=12)
        tk.Label(card.body,text='显示列',bg='white',fg='#17213C',font=('Segoe UI Semibold',13)).pack(anchor='w',pady=(0,8))
        if not hasattr(self,'column_visibility'):
            try: saved=json.loads(self.UI_SETTINGS.read_text(encoding='utf-8')).get('columns',{})
            except Exception: saved={}
            self.column_visibility={c:tk.BooleanVar(value=saved.get(c,True)) for _,c in columns}
        for label,column in columns:
            row=tk.Frame(card.body,bg='white');row.pack(fill='x',pady=4);tk.Label(row,text=label,bg='white',fg=COLORS['text']).pack(side='left');ToggleSwitch(row,self.column_visibility[column],command=self._apply_column_visibility).pack(side='right')
        popup.geometry(f'280x330+{self.winfo_pointerx()-280}+{self.winfo_pointery()+8}')

    def _apply_column_visibility(self):
        if hasattr(self,'column_visibility'):
            try:
                data=json.loads(self.UI_SETTINGS.read_text(encoding='utf-8')) if self.UI_SETTINGS.exists() else {};data['columns']={c:v.get() for c,v in self.column_visibility.items()};self.UI_SETTINGS.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
            except OSError:pass
        base=['file','date','kind','recommend']; width=self.winfo_width()
        optional=['place','device','quality','duplicate','burst']
        if width < 1280: optional=['quality']
        elif width < 1600: optional=['place','quality','duplicate','burst']
        visible=base[:]
        for column in optional:
            if not hasattr(self,'column_visibility') or self.column_visibility.get(column,tk.BooleanVar(value=True)).get(): visible.insert(-1,column)
        if not self.smart.get(): visible=[c for c in visible if c not in ('quality','duplicate','burst')]
        self.tree.configure(displaycolumns=tuple(visible))
        widths={'#0':88,'file':210,'date':110,'place':120,'device':140,'kind':80,'quality':90,'duplicate':90,'burst':90,'recommend':110}
        for column,value in widths.items():
            try:
                self.tree.heading(column, anchor='center')
                self.tree.column(column,width=value,minwidth=min(value,60),stretch=column=='file',anchor='center')
            except tk.TclError:pass
    def _open_batch_adjustment(self):
        dialog=tk.Toplevel(self);dialog.title('批量调整');dialog.transient(self);dialog.resizable(False,False);dialog.configure(bg=COLORS['app_bg'])
        dialog.geometry(f'620x330+{self.winfo_rootx()+420}+{self.winfo_rooty()+240}')
        card=RoundedCard(dialog,padding=18);card.pack(fill='both',expand=True,padx=14,pady=14)
        tk.Label(card.body,text='批量调整',bg='white',fg='#17213C',font=('Segoe UI Semibold',14)).pack(anchor='w')
        selected_text=tk.StringVar(value=f'已选择 {len(self.tree.selection())} 个素材')
        tk.Label(card.body,textvariable=selected_text,bg='white',fg=COLORS['muted'],font=('Segoe UI',9)).pack(anchor='w',pady=(3,12))
        actions=tk.Frame(card.body,bg='white');actions.pack(fill='x')
        def update_state():
            count=len(self.tree.selection());selected_text.set(f'已选择 {count} 个素材');apply_btn.configure(state='normal' if count else 'disabled');restore_btn.configure(state='normal' if count and bool(getattr(self,'batch_undo',{})) else 'disabled')
        def select_all(): self.tree.selection_set(self.tree.get_children());update_state()
        def clear(): self.tree.selection_remove(self.tree.selection());update_state()
        rename_cmd=getattr(self,'rename_selected_folder',lambda:messagebox.showinfo('重命名文件夹','请先在左侧选择自定义文件夹。',parent=dialog))
        CanvasButton(actions,'重命名文件夹',width=120,height=36,command=rename_cmd).pack(side='left')
        CanvasButton(actions,'全选',width=80,height=36,command=select_all).pack(side='left',padx=(8,0))
        CanvasButton(actions,'清空选择',width=96,height=36,command=clear).pack(side='left',padx=(8,0))
        if hasattr(self,'batch_select_mode'):
            row=tk.Frame(card.body,bg='white');row.pack(fill='x',pady=(14,4));ToggleSwitch(row,self.batch_select_mode).pack(side='left');tk.Label(row,text='批量选择模式',bg='white',fg=COLORS['text']).pack(side='left',padx=8)
        place=tk.Frame(card.body,bg='white');place.pack(fill='x',pady=14)
        tk.Label(place,text='批量设置地点：',bg='white',fg=COLORS['text']).pack(side='left')
        value=tk.StringVar();entry=tk.Entry(place,textvariable=value,relief='flat',highlightthickness=1,highlightbackground=COLORS['border']);entry.pack(side='left',fill='x',expand=True,ipady=8)
        def apply_place():
            selected=list(self.tree.selection())
            if not selected:return
            summary=f'将 {len(selected)} 个素材的地点修改为“{value.get().strip() or "空白"}”。\n\n是否应用？'
            if not messagebox.askyesno('确认批量修改',summary,parent=dialog):return
            self.batch_undo={}
            for iid in selected:
                try:
                    index=int(iid);self.batch_undo[index]=self.rows[index].get('place','');self.rows[index]['place']=value.get().strip()
                except (ValueError,IndexError):pass
            self.calculate();self.render();update_state()
        def restore():
            for index,old in getattr(self,'batch_undo',{}).items():
                if 0<=index<len(self.rows):self.rows[index]['place']=old
            self.batch_undo={};self.calculate();self.render();update_state()
        apply_btn=CanvasButton(place,'应用',variant='primary',width=80,height=36,command=apply_place);apply_btn.pack(side='left',padx=(8,0))
        restore_btn=CanvasButton(place,'恢复',width=80,height=36,command=restore);restore_btn.pack(side='left',padx=(8,0));update_state()
    def _v3_selection_changed(self, _event=None):
        selected = list(self.tree.selection())
        if hasattr(self, 'v3_selection_text'):
            self.v3_selection_text.set(f'已选择 {len(selected)} 个素材')
        has_video = False
        for iid in selected:
            try:
                if self.rows[int(iid)].get('kind') == '视频': has_video = True; break
            except (ValueError, IndexError): pass
        if hasattr(self, 'keyframes_button_v3'):
            self.keyframes_button_v3.configure(state='normal' if selected and has_video and not self.scan_busy else 'disabled')
            self.open_original_button_v3.configure(state='normal' if selected else 'disabled')
            self.remove_plan_button_v3.configure(state='normal' if selected and not self.scan_busy else 'disabled')

    def _sync_v3_counts(self):
        if not hasattr(self, 'v3_stat_values'):
            return
        photos = sum(row.get('kind') == '照片' for row in self.rows)
        videos = sum(row.get('kind') == '视频' for row in self.rows)
        failed = sum(not row.get('analysis', {}).get('valid', True) or row.get('recommend') == '无法解码' for row in self.rows)
        for variable, value in zip(self.v3_stat_values, (len(self.rows), photos, videos, failed)):
            variable.set(str(value))
        self.v3_total_text.set(f'共 {len(self.tree.get_children())} 条')
    def refresh_sidebar(self):
        super().refresh_sidebar()
        if hasattr(self, 'sidebar_list') and self.sidebar_list.size() and not self.sidebar_list.curselection():
            self.sidebar_list.yview_moveto(0)
        if hasattr(self, 'folder_tree_panel'):
            self.folder_tree_panel.set_data(self.output_directories())

    def select_folder_target(self, target):
        for index, (kind, value) in enumerate(self.sidebar_targets):
            if kind == 'target' and value == target:
                self.sidebar_list.selection_clear(0, 'end'); self.sidebar_list.selection_set(index)
                self.sidebar_select(); return


    def render(self):
        super().render()
        self.after_idle(self._sync_v3_counts)
        self.after_idle(self._apply_column_visibility)

    def apply_filter(self):
        super().apply_filter()
        self.after_idle(self._sync_v3_counts)
        self.after_idle(self._apply_column_visibility)
    def _responsive_layout(self):
        if not hasattr(self, 'setup_cards'):
            return
        for card in (self.source_card, self.rule_card):
            card.pack_forget()
        if self.content_v3.winfo_width() < 1040:
            self.source_card.pack(fill='x', pady=(0, 12))
            self.rule_card.pack(fill='x')
        else:
            self.source_card.pack(side='left', fill='both', expand=True, padx=(0, 8))
            self.rule_card.pack(side='left', fill='both', expand=True, padx=(8, 0))

    def _install_traces(self):
        self.out.trace_add('write', lambda *_: self._refresh_scan_availability())
        self.english.trace_add('write', lambda *_: self._refresh_scan_availability())

    def _refresh_path_lists(self):
        if hasattr(self, 'source_list_v3'):
            self.source_list_v3.refresh(); self.exclude_list_v3.refresh()
            self.source_count_label.configure(text=f'已添加的素材来源（{len(self.sources)}）')
        self._refresh_scan_availability()

    def _remove_source_index(self, index):
        if 0 <= index < len(self.sources):
            del self.sources[index]
            try: self.src_box.delete(index)
            except tk.TclError: pass
            self._refresh_path_lists()

    def _remove_exclude_index(self, index):
        if 0 <= index < len(self.excludes):
            del self.excludes[index]
            try: self.exc_box.delete(index)
            except tk.TclError: pass
            self._refresh_path_lists()

    def add_source(self):
        before = len(self.sources)
        super().add_source()
        if len(self.sources) != before: self._refresh_path_lists()

    def add_exclusion(self):
        before = len(self.excludes)
        super().add_exclusion()
        if len(self.excludes) != before: self._refresh_path_lists()

    def drop_src(self, event):
        result = super().drop_src(event); self._refresh_path_lists(); return result

    def drop_exc(self, event):
        result = super().drop_exc(event); self._refresh_path_lists(); return result

    def output(self):
        result = super().output(); self._refresh_scan_availability(); return result

    def _validation_error(self):
        if not self.sources: return '请至少添加一个素材来源'
        output = str(self.out.get()).strip()
        if not output: return '请设置有效的保存位置'
        try:
            output_path = Path(output).resolve()
            for source in self.sources:
                for excluded in self.excludes:
                    if Path(source).resolve() == Path(excluded).resolve():
                        return '素材来源与排除目录存在冲突'
            parent = output_path if output_path.exists() else output_path.parent
            if not parent.exists(): return '保存位置的上级目录不存在'
        except (OSError, ValueError): return '保存路径无效'
        return ''

    def _refresh_scan_availability(self):
        if not hasattr(self, 'scan_button'): return
        error = self._validation_error()
        self.validation_label.configure(text=error if hasattr(self, 'validation_label') else '')
        self.scan_button.configure(state='disabled' if error or self.scan_busy else 'normal')

    def _save_draft(self):
        try:
            self._save_output_path()
        except Exception:
            pass
        messagebox.showinfo('已保存', '当前保存位置和整理设置已保存。', parent=self)

    def start_scan(self):
        error = self._validation_error()
        if error:
            return messagebox.showwarning('无法开始扫描', error, parent=self)
        self.scan_started_at = time.monotonic()
        self.scan_pause.clear()
        self.v3_state.set('正在扫描素材')
        self.v3_phase.set('建立素材清单')
        self.v3_task.set('正在读取文件信息与生成预览')
        self.state_badge.configure(text='AI 识别中', bg=COLORS['soft_blue'], fg=COLORS['blue'])
        self.pause_button.configure(text='暂停扫描', icon='pause', state='normal')
        self.stop_scan_button.configure(state='normal')
        self.rescan_button.configure(state='disabled')
        if hasattr(self,'execute_button_v3'): self.execute_button_v3.configure(state='disabled')
        if hasattr(self,'output_change_button'): self.output_change_button.configure(state='disabled')
        self._select_page(1)
        super().start_scan()
        self._refresh_scan_availability()

    def update(self, *args):
        if len(args) == 3:
            while self.scan_pause.is_set() and self.scan_busy:
                time.sleep(.08)
            return super().update(*args)
        return tk.Tk.update(self)

    def toggle_pause(self):
        if not self.scan_busy: return
        if self.scan_pause.is_set():
            self.scan_pause.clear(); self.v3_state.set('正在扫描素材'); self.pause_button.configure(text='暂停扫描', icon='pause')
            self.state_badge.configure(text='AI 识别中')
        else:
            self.scan_pause.set(); self.v3_state.set('扫描已暂停'); self.pause_button.configure(text='继续扫描', icon='play')
            self.state_badge.configure(text='已暂停')

    def stop_scan(self):
        if not self.scan_busy: return
        self.stop.set(); self.scan_pause.clear()
        self.v3_state.set('正在停止扫描')
        self.state_badge.configure(text='停止中', bg='#FFF1F0', fg=COLORS['warning'])
        self.v3_task.set('正在安全结束当前任务，已完成的识别结果会保留')
        self.pause_button.configure(state='disabled')
        self.stop_scan_button.configure(state='disabled')
    def _show_progress(self, number, total, text):
        super()._show_progress(number, total, text)
        total = max(1, int(total or 1)); number = max(0, int(number or 0)); percent = min(100, number * 100 / total)
        self.v3_progress_value.set(percent)
        self.v3_progress_text.set(f'{number} / {total}')
        self.v3_percent_text.set(f'{percent:.0f}%')
        self.v3_task.set(str(text))
        if '视频' in str(text): self.v3_phase.set('视频镜头与关键帧分析')
        elif '识别' in str(text): self.v3_phase.set('AI 识别与分类')
        else: self.v3_phase.set('建立素材清单')
        elapsed = max(.1, time.monotonic() - (self.scan_started_at or time.monotonic()))
        if number > 0 and total > number:
            remain = elapsed / number * (total - number)
            self.v3_eta.set(f'预计剩余 {max(1, round(remain / 60))} 分钟')
        else: self.v3_eta.set('')

    def _finish_scan(self, error):
        super()._finish_scan(error)
        self.scan_pause.clear(); self.pause_button.configure(state='disabled', icon='pause', text='暂停扫描')
        self.stop_scan_button.configure(state='disabled')
        self.rescan_button.configure(text='重新扫描', icon='rescan', state='normal')
        if hasattr(self,'output_change_button'): self.output_change_button.configure(state='normal')
        if hasattr(self,'execute_button_v3'):
            ready = error is None and not self.stop.is_set()
            self.execute_button_v3.configure(text='执行整理' if ready else '扫描并预览', command=(self._execute_legacy.invoke if ready and self._execute_legacy else self.start_scan), state='normal' if ready else 'disabled')
        if error is not None:
            self.v3_state.set('扫描失败'); self.state_badge.configure(text='需要处理', bg='#FFF1F0', fg=COLORS['warning'])
            self.v3_task.set(str(error))
        elif self.stop.is_set():
            self.v3_state.set('扫描已停止'); self.state_badge.configure(text='已停止')
        else:
            self.v3_state.set('扫描完成'); self.state_badge.configure(text='已完成', bg='#E9F5EF', fg=COLORS['success'])
            self.v3_progress_value.set(100); self.v3_percent_text.set('100%')
            elapsed = time.monotonic() - (self.scan_started_at or time.monotonic())
            failed = len(getattr(self, 'failed', []))
            self.v3_task.set(f'扫描耗时 {elapsed:.1f} 秒，异常 {failed} 项')
            self.v3_eta.set('')
        self.scan_button.configure(text='开始扫描')
        self._refresh_scan_availability()


SafeDragV36MediaOrganizerApp().mainloop()
