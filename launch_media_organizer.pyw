import builtins
from pathlib import Path

from performance_cache import cached_analysis, cached_scene_class, cached_sha, cached_video

root = Path(__file__).resolve().parent
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

audited_path = root / 'launch_ai_entry_audited.pyw'
source = audited_path.read_text(encoding='utf-8').rsplit('AuditedAIApp().mainloop()', 1)[0]
scope = {'__file__': str(audited_path)}
exec(compile(source, str(audited_path), 'exec'), scope)
AuditedAIApp = scope['AuditedAIApp']


def find_owner(name):
    return next(cls for cls in AuditedAIApp.__mro__ if name in cls.__dict__)


batch2_scan = next(cls.__dict__['scan'] for cls in AuditedAIApp.__mro__ if cls.__name__ == 'Batch2App')
batch2_scan.__globals__['sha'] = cached_sha(batch2_scan.__globals__['sha'])
batch2_scan.__globals__['analyze'] = cached_analysis(batch2_scan.__globals__['analyze'])

batch3_scan = next(cls.__dict__['scan'] for cls in AuditedAIApp.__mro__ if cls.__name__ == 'Batch3App')
batch3_scan.__globals__['analyze_video'] = cached_video(batch3_scan.__globals__['analyze_video'])

scene_scan = next(cls.__dict__['scan'] for cls in AuditedAIApp.__mro__ if cls.__name__ == 'SceneFolderApp')
scene_scan.__globals__['SceneRecognizer'] = cached_scene_class(scene_scan.__globals__['SceneRecognizer'])

for cls in AuditedAIApp.__mro__:
    run = cls.__dict__.get('run')
    if run and 'sha' in run.__globals__:
        run.__globals__['sha'] = cached_sha(run.__globals__['sha'])


class MediaOrganizerApp(AuditedAIApp):
    def __init__(self):
        super().__init__()
        self.title('Media Organizer · Windows')
        self.status.set('已启用智能缓存；未变化的素材不会重复识别')


MediaOrganizerApp().mainloop()
