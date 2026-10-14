import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')
launcher = root / 'launch_media_organizer_fixed_minus_column.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('FixedMinusColumnMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
FixedMinusColumnMediaOrganizerApp = scope['FixedMinusColumnMediaOrganizerApp']


class ResizableTableMediaOrganizerApp(FixedMinusColumnMediaOrganizerApp):
    MIN_TABLE_ROWS = 4
    MAX_TABLE_ROWS = 32
    ROW_PIXELS = 31

    def __init__(self):
        super().__init__()
        # Remove the obsolete sentence that referred to the deleted card panel.
        for child in self.resize_grip.winfo_children():
            if child.winfo_class() == 'TLabel':
                child.destroy()
        self.resize_grip.configure(height=9, cursor='sb_v_double_arrow')
        self.resize_grip.pack_configure(pady=(2, 2))
        for child in self.resize_grip.winfo_children():
            child.configure(cursor='sb_v_double_arrow')
            child.bind('<ButtonPress-1>', self.start_panel_resize)
            child.bind('<B1-Motion>', self.resize_panels)
        self.resize_start_tree_rows = 10

    def start_panel_resize(self, event):
        self.resize_start_y = event.y_root
        actual_rows = round(max(1, self.tree.winfo_height()) / self.ROW_PIXELS)
        configured_rows = int(self.tree.cget('height') or 10)
        self.resize_start_tree_rows = max(self.MIN_TABLE_ROWS, min(self.MAX_TABLE_ROWS, actual_rows or configured_rows))
        self.tree.pack_configure(expand=False)

    def resize_panels(self, event):
        delta_rows = round((event.y_root - self.resize_start_y) / self.ROW_PIXELS)
        rows = self.resize_start_tree_rows - delta_rows
        rows = max(self.MIN_TABLE_ROWS, min(self.MAX_TABLE_ROWS, rows))
        self.tree.configure(height=rows)
        self.status.set(f'素材表格高度：{rows} 行；继续拖动横线可调整')


ResizableTableMediaOrganizerApp().mainloop()
