import json
import sqlite3
import threading
from pathlib import Path


CACHE_VERSION = 2
CACHE_PATH = Path(__file__).resolve().parent / 'test-results' / 'cache' / 'media-cache.sqlite3'
LOCK = threading.RLock()


def _fingerprint(path):
    path = Path(path)
    stat = path.stat()
    return str(path.resolve()), stat.st_mtime_ns, stat.st_size


def _connect():
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(CACHE_PATH, timeout=30)
    connection.execute('PRAGMA journal_mode=WAL')
    connection.execute(
        'CREATE TABLE IF NOT EXISTS cache ('
        'path TEXT NOT NULL, mtime_ns INTEGER NOT NULL, size INTEGER NOT NULL, '
        'kind TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL, '
        'PRIMARY KEY(path, kind))'
    )
    return connection


def get(path, kind):
    key, mtime_ns, size = _fingerprint(path)
    with LOCK, _connect() as connection:
        row = connection.execute(
            'SELECT payload FROM cache WHERE path=? AND mtime_ns=? AND size=? AND kind=? AND version=?',
            (key, mtime_ns, size, kind, CACHE_VERSION),
        ).fetchone()
    return json.loads(row[0]) if row else None


def put(path, kind, value):
    key, mtime_ns, size = _fingerprint(path)
    payload = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    with LOCK, _connect() as connection:
        connection.execute(
            'INSERT OR REPLACE INTO cache(path,mtime_ns,size,kind,version,payload) VALUES(?,?,?,?,?,?)',
            (key, mtime_ns, size, kind, CACHE_VERSION, payload),
        )
        connection.commit()
    return value


def cached_sha(original):
    def wrapper(path):
        value = get(path, 'sha256')
        if value is None:
            value = original(path)
            put(path, 'sha256', value)
        return value
    return wrapper


def cached_analysis(original):
    def wrapper(path, media_kind, exact_hash):
        value = get(path, 'analysis')
        if value is None:
            value = original(path, media_kind, exact_hash)
            put(path, 'analysis', value)
        return value
    return wrapper


def cached_video(original):
    def wrapper(path, cache_root, max_scenes=100):
        value = get(path, 'video')
        if value is not None:
            frames = value.get('keyframes', [])
            if not frames or all(Path(frame).exists() for frame in frames):
                return value
        value = original(path, cache_root, max_scenes=max_scenes)
        put(path, 'video', value)
        return value
    return wrapper


def cached_scene_class(base_class):
    class CachedSceneRecognizer(base_class):
        def classify_image(self, path):
            value = get(path, 'scene')
            if value is None:
                value = super().classify_image(path)
                put(path, 'scene', value)
            return value

        def classify_video(self, row, max_frames=3):
            path = row['p']
            value = get(path, 'scene')
            if value is None:
                value = super().classify_video(row, max_frames=max_frames)
                put(path, 'scene', value)
            return value

    return CachedSceneRecognizer

