import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_inline_add_remove.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('InlineAddRemoveMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
InlineAddRemoveMediaOrganizerApp = scope['InlineAddRemoveMediaOrganizerApp']


class SetupFixedMediaOrganizerApp(InlineAddRemoveMediaOrganizerApp):
    def retarget(self):
        if hasattr(self, 'book') and self.book.select() == str(self.setup):
            language = 'English folders' if self.english.get() else '中文目录'
            self.status.set(f'目录命名已选择：{language}；点击“扫描并预览”后生效')
            return
        super().retarget()


SetupFixedMediaOrganizerApp().mainloop()
