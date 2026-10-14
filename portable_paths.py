import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL_NAMES = (
    'deploy_googlenet_places365.prototxt',
    'googlenet_places365.caffemodel',
    'categories_places365.txt',
    'face_detection_yunet_2026may.onnx',
    'face_recognition_sface_2021dec.onnx',
)


def portable_model_root():
    local_scene = ROOT / 'tools' / 'scene-models'
    local_tools = ROOT / 'tools'
    public = Path(os.environ.get('PUBLIC', r'C:\Users\Public')) / 'MediaOrganizerModels'
    try:
        public.mkdir(parents=True, exist_ok=True)
        for name in MODEL_NAMES:
            source = (local_scene / name) if (local_scene / name).exists() else (local_tools / name)
            target = public / name
            if source.exists() and (not target.exists() or target.stat().st_size != source.stat().st_size):
                shutil.copy2(source, target)
        if all((public / name).exists() for name in MODEL_NAMES):
            return public
    except OSError:
        pass
    fallback = Path.home() / '.libtv' / 'media-organizer-models'
    if all((fallback / name).exists() for name in MODEL_NAMES):
        return fallback
    return local_scene


def find_ffprobe():
    candidates = [ROOT / 'tools' / 'ffprobe.exe']
    found = shutil.which('ffprobe')
    if found:
        candidates.append(Path(found))
    return next((path for path in candidates if path.exists()), None)
