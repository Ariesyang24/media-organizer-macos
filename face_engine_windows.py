import sqlite3
from pathlib import Path

import cv2
from face_engine import FaceEngine, cluster

ROOT = Path(__file__).resolve().parent
LOCAL_MODELS = ROOT / 'tools'
FALLBACK_MODELS = Path(r'C:\Users\admin\.libtv\media-organizer-models')
MODEL_ROOT = LOCAL_MODELS if (LOCAL_MODELS / 'face_detection_yunet_2026may.onnx').exists() else FALLBACK_MODELS


class WindowsFaceEngine(FaceEngine):
    def __init__(self, cache_path):
        detector = str(MODEL_ROOT / 'face_detection_yunet_2026may.onnx')
        recognizer = str(MODEL_ROOT / 'face_recognition_sface_2021dec.onnx')
        self.detector = cv2.FaceDetectorYN.create(detector, '', (320, 320), 0.8, 0.3, 5000)
        self.recognizer = cv2.FaceRecognizerSF.create(recognizer, '')
        self.db = sqlite3.connect(cache_path)
        self.db.execute('create table if not exists faces(path text,mtime real,size integer,idx integer,embedding blob,box text,primary key(path,idx))')
        self.db.commit()
