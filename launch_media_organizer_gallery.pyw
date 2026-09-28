import builtins
from pathlib import Path

from thumbnail_gallery import ThumbnailGallery

root = Path(__file__).resolve().parent
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

top_path = root / 'launch_media_organizer_top_button.pyw'
source = top_path.read_text(encoding='utf-8').rsplit('TopButtonMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(top_path)}
exec(compile(source, str(top_path), 'exec'), scope)
TopButtonMediaOrganizerApp = scope['TopButtonMediaOrganizerApp']


class GalleryMediaOrganizerApp(TopButtonMediaOrganizerApp):
    def __init__(self):
        super().__init__()
        self.stage_text = self._install_stage_label()
        self.gallery = None

    def _install_stage_label(self):
        variable = tk.StringVar(value='当前阶段：等待扫描')
        panel = self.progress.master
        labels = [child for child in panel.winfo_children() if child.winfo_class() == 'TLabel']
        if labels:
            labels[0].configure(textvariable=variable, width=34)
        return variable

    def _show_progress(self, number, total, text):
        super()._show_progress(number, total, text)
        if text.startswith('扫描 '):
            stage = '建立素材清单'
        elif text.startswith('第二批识别'):
            stage = '画质、重复、连拍与人物'
        elif text.startswith('视频分析'):
            stage = '视频镜头与关键帧'
        elif text.startswith('内容场景识别'):
            stage = 'AI内容场景'
        elif '完成' in text:
            stage = '识别完成'
        else:
            stage = '正在处理'
        percent = int(number * 100 / max(1, total))
        self.stage_text.set(f'当前阶段：{stage}  {number}/{total}  ({percent}%)')

    def start_scan(self):
        self.stage_text.set('当前阶段：正在准备扫描…')
        super().start_scan()

    def _finish_scan(self, error):
        super()._finish_scan(error)
        if error is None and not self.stop.is_set():
            self.stage_text.set(f'当前阶段：识别完成  {len(self.rows)}/{len(self.rows)}  (100%)')

    def _show_gallery(self, title, rows):
        if self.gallery is not None and not self.gallery.closed:
            self.gallery.close()
        self.gallery = ThumbnailGallery(self, title, rows)

    def open_category(self, category):
        if category == '全部':
            rows = self.rows
        elif category == '照片':
            rows = [row for row in self.rows if row.get('kind') == '照片']
        elif category == '视频':
            rows = [row for row in self.rows if row.get('kind') == '视频']
        else:
            rows = [row for row in self.rows if not row.get('analysis', {}).get('valid', True) or row.get('recommend') == '无法解码']
        self._show_gallery(category, rows)

    def open_scene(self, scene):
        rows = [row for row in self.rows if row.get('scene', {}).get('group') == scene]
        self._show_gallery(scene, rows)


GalleryMediaOrganizerApp().mainloop()
