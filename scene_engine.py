from collections import Counter
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent
from portable_paths import portable_model_root
MODEL_ROOT = portable_model_root()
PROTO = MODEL_ROOT / 'deploy_googlenet_places365.prototxt'
MODEL = MODEL_ROOT / 'googlenet_places365.caffemodel'
LABELS = MODEL_ROOT / 'categories_places365.txt'

SCENE_RULES = {
    '餐饮美食': ('restaurant', 'kitchen', 'dining', 'cafeteria', 'coffee_shop', 'bakery', 'food_court', 'bar/', 'banquet'),
    '商业购物': ('shop', 'store', 'market', 'supermarket', 'showroom', 'shopping_mall', 'boutique', 'beauty_salon', 'bank_vault'),
    '街景交通': ('street', 'highway', 'road', 'crosswalk', 'parking', 'subway', 'train_station', 'airport', 'airplane', 'cockpit', 'berth', 'bus_', 'vehicle'),
    '自然风景': ('beach', 'forest', 'mountain', 'field', 'river', 'lake', 'ocean', 'waterfall', 'desert', 'garden', 'park', 'canyon', 'valley'),
    '建筑地标': ('building', 'tower', 'bridge', 'church', 'synagogue', 'temple', 'palace', 'castle', 'plaza', 'courtyard', 'monument', 'museum', 'medina'),
    '运动活动': ('stadium', 'gym', 'sports', 'swimming_pool', 'ski', 'racecourse', 'playground', 'bowling'),
    '舞台娱乐': ('stage', 'theater', 'cinema', 'amusement', 'discotheque', 'music_studio', 'television_studio', 'auditorium'),
    '办公学习': ('office', 'reception', 'classroom', 'library', 'conference_room', 'computer_room', 'art_studio'),
    '家居室内': ('bedroom', 'bedchamber', 'living_room', 'bathroom', 'home_office', 'closet', 'dressing_room', 'utility_room', 'nursery', 'playroom', 'attic', 'basement'),
    '动物宠物': ('aquarium', 'zoo', 'pet_shop', 'stable', 'barn', 'kennel'),
}


TOP_K = 7

class SceneRecognizer:
    def __init__(self):
        if not all(path.exists() for path in (PROTO, MODEL, LABELS)):
            raise FileNotFoundError('场景识别模型不完整')
        self.net = cv2.dnn.readNetFromCaffe(str(PROTO), str(MODEL))
        self.labels = []
        for line in LABELS.read_text(encoding='utf-8').splitlines():
            token = line.split()[0].lstrip('/').split('/', 1)[-1]
            self.labels.append(token)

    @staticmethod
    def _read_image(path):
        data = np.fromfile(str(path), dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)

    @staticmethod
    def _group(label):
        normalized = label.lower()
        for group, words in SCENE_RULES.items():
            if any(word in normalized for word in words):
                return group
        indoor_words = ('room', 'indoor', 'corridor', 'hall', 'lobby', 'elevator', 'staircase')
        return '室内其他' if any(word in normalized for word in indoor_words) else '其他场景'

    def classify_frame(self, frame):
        if frame is None or frame.size == 0:
            return {'group': '无法识别', 'label': '', 'confidence': 0.0}
        blob = cv2.dnn.blobFromImage(frame, 1.0, (224, 224), (104, 117, 123), swapRB=False, crop=True)
        self.net.setInput(blob)
        scores = self.net.forward().reshape(-1)
        count = min(TOP_K, len(scores))
        top = np.argpartition(scores, -count)[-count:]
        top = top[np.argsort(scores[top])[::-1]]
        candidates, group_scores, group_best = [], Counter(), {}
        for index in top:
            index = int(index)
            label = self.labels[index] if index < len(self.labels) else 'unknown'
            confidence = float(scores[index])
            group = self._group(label)
            item = {'group': group, 'label': label, 'confidence': confidence}
            candidates.append(item)
            group_scores[group] += confidence
            if group not in group_best or confidence > group_best[group]['confidence']:
                group_best[group] = item
        group = group_scores.most_common(1)[0][0]
        representative = group_best[group]
        return {'group': group, 'label': representative['label'],
                'confidence': float(group_scores[group]), 'candidates': candidates}

    def classify_image(self, path):
        return self.classify_frame(self._read_image(path))

    def classify_video(self, row, max_frames=5):
        keyframes = row.get('video_analysis', {}).get('keyframes', [])
        results = []
        if keyframes:
            results = [self.classify_image(path) for path in keyframes[:max_frames]]
        else:
            cap = cv2.VideoCapture(str(row['p']))
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            for ratio in (0.10, 0.30, 0.50, 0.70, 0.90):
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(total * ratio)))
                ok, frame = cap.read()
                if ok:
                    results.append(self.classify_frame(frame))
            cap.release()
        valid = [item for item in results if item['group'] != '无法识别']
        if not valid:
            return {'group': '无法识别', 'label': '', 'confidence': 0.0}
        votes = Counter()
        for item in valid:
            votes[item['group']] += max(0.01, item['confidence'])
        group = votes.most_common(1)[0][0]
        representative = max((item for item in valid if item['group'] == group), key=lambda item: item['confidence'])
        return {'group': group, 'label': representative['label'], 'confidence': representative['confidence']}
