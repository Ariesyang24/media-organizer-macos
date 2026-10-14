import builtins
import shutil
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

runtime_models = Path(tempfile.gettempdir()) / 'MediaOrganizerModels'
runtime_models.mkdir(parents=True, exist_ok=True)


def ensure_model(source):
    source = Path(source)
    target = runtime_models / source.name
    if source.exists() and (not target.exists() or target.stat().st_size != source.stat().st_size):
        shutil.copy2(source, target)
    return target


face_detector = ensure_model(root / 'tools' / 'face_detection_yunet_2026may.onnx')
face_recognizer = ensure_model(root / 'tools' / 'face_recognition_sface_2021dec.onnx')
scene_proto = ensure_model(root / 'tools' / 'scene-models' / 'deploy_googlenet_places365.prototxt')
scene_model = ensure_model(root / 'tools' / 'scene-models' / 'googlenet_places365.caffemodel')
scene_labels = ensure_model(root / 'tools' / 'scene-models' / 'categories_places365.txt')

import face_engine_windows
face_engine_windows.MODEL_ROOT = runtime_models

import scene_engine
scene_engine.MODEL_ROOT = runtime_models
scene_engine.PROTO = scene_proto
scene_engine.MODEL = scene_model
scene_engine.LABELS = scene_labels

thumbnail_path = root / 'launch_media_organizer_thumbnail_review.pyw'
source = thumbnail_path.read_text(encoding='utf-8').rsplit('ThumbnailReviewMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(thumbnail_path)}
exec(compile(source, str(thumbnail_path), 'exec'), scope)
scope['ThumbnailReviewMediaOrganizerApp']().mainloop()
