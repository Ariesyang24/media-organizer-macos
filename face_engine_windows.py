import sqlite3
from pathlib import Path

import cv2
from face_engine import ENGINE_VERSION, FaceEngine, cluster

ROOT = Path(__file__).resolve().parent
from portable_paths import portable_model_root
MODEL_ROOT = portable_model_root()


class WindowsFaceEngine(FaceEngine):
    def __init__(self, cache_path):
        detector = str(MODEL_ROOT / 'face_detection_yunet_2026may.onnx')
        recognizer = str(MODEL_ROOT / 'face_recognition_sface_2021dec.onnx')
        self.detector = cv2.FaceDetectorYN.create(detector, '', (320, 320), 0.65, 0.3, 5000)
        self.recognizer = cv2.FaceRecognizerSF.create(recognizer, '')
        self.db = sqlite3.connect(cache_path)
        self.db.execute('create table if not exists faces(path text,mtime real,size integer,idx integer,embedding blob,box text,primary key(path,idx))')
        self.db.execute('create table if not exists face_meta(key text primary key,value text)')
        version = self.db.execute("select value from face_meta where key='engine_version'").fetchone()
        if not version or version[0] != ENGINE_VERSION:
            self.db.execute('delete from faces')
        self.db.execute("insert or replace into face_meta values('engine_version',?)", (ENGINE_VERSION,))
        self.db.commit()
