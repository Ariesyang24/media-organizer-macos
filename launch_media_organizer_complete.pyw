import builtins
import threading
from pathlib import Path

root = Path(__file__).resolve().parent
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

gallery_path = root / 'launch_media_organizer_gallery.pyw'
source = gallery_path.read_text(encoding='utf-8').rsplit('GalleryMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(gallery_path)}
exec(compile(source, str(gallery_path), 'exec'), scope)
GalleryMediaOrganizerApp = scope['GalleryMediaOrganizerApp']


class CompleteMediaOrganizerApp(GalleryMediaOrganizerApp):
    def _finish_scan(self, error):
        if error is not None or self.stop.is_set():
            super()._finish_scan(error)
            return
        missing = [row for row in self.rows if not row.get('scene')]
        if self.scene_on.get() and missing:
            self.scan_busy = True
            self.scan_button.configure(text='正在补齐AI识别…', state='disabled')
            self.stage_text.set(f'当前阶段：补齐AI内容场景  0/{len(missing)}  (0%)')
            threading.Thread(target=self._recover_scenes, args=(missing,), daemon=True).start()
            return
        self._finalize_complete()

    def _recover_scenes(self, missing):
        error = None
        try:
            scene_scan = next(cls.__dict__['scan'] for cls in self.__class__.__mro__ if cls.__name__ == 'SceneFolderApp')
            recognizer = scene_scan.__globals__['SceneRecognizer']()
            total = len(missing)
            for index, row in enumerate(missing, 1):
                if self.stop.is_set():
                    break
                if row.get('faces'):
                    result = {'group': '人物', 'label': 'person', 'confidence': 1.0}
                elif row.get('kind') == '视频':
                    result = recognizer.classify_video(row)
                else:
                    result = recognizer.classify_image(row['p'])
                row['scene'] = result
                self.update(index, total, f'内容场景识别 {index}/{total}：{row["p"].name}')
        except Exception as exc:
            error = exc
        self.after(0, lambda caught=error: self._finish_recovery(caught))

    def _finish_recovery(self, error):
        if error is not None:
            super()._finish_scan(error)
            return
        self._finalize_complete()

    def _finalize_complete(self):
        self.render()
        super()._finish_scan(None)
        scene_count = sum(bool(row.get('scene')) for row in self.rows)
        if self.scene_on.get() and scene_count != len(self.rows):
            self.stage_text.set(f'当前阶段：AI场景未完成  {scene_count}/{len(self.rows)}')
            self.status.set(f'AI场景识别未完成：{scene_count}/{len(self.rows)}')
        else:
            self.stage_text.set(f'当前阶段：全部识别完成  {len(self.rows)}/{len(self.rows)}  (100%)')
            self.status.set('全部识别已完成，可点击文件夹查看缩略图')


CompleteMediaOrganizerApp().mainloop()
