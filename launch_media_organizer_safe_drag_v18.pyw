import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

launcher = root / 'launch_media_organizer_safe_drag_v17.pyw'
source = launcher.read_text(encoding='utf-8').rsplit('SafeDragV17MediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(launcher)}
exec(compile(source, str(launcher), 'exec'), scope)
SafeDragV17MediaOrganizerApp = scope['SafeDragV17MediaOrganizerApp']


class SafeDragV18MediaOrganizerApp(SafeDragV17MediaOrganizerApp):
    COLUMN_TITLES = {
        'file': '文件名',
        'date': '拍摄日期',
        'place': '地点',
        'device': '设备',
        'kind': '类型',
        'quality': '画质',
        'duplicate': '重复组',
        'burst': '连拍组',
        'people': '人物',
        'recommend': '处理建议',
        'target': '整理位置',
        'video': '视频分析',
        'ai_scene': '场景识别',
    }

    def __init__(self):
        super().__init__()
        self.tree.heading('#0', text='预览')
        for column in self.tree['columns']:
            self.tree.heading(column, text=self.COLUMN_TITLES.get(column, column))


SafeDragV18MediaOrganizerApp().mainloop()
