import hashlib
import json
from pathlib import Path


CATALOG_FILE = Path(__file__).resolve().parent / 'test-results' / 'project-folder-catalog.json'


def project_key(sources):
    normalized = sorted(str(Path(source).resolve()).casefold() for source in sources)
    if not normalized:
        return ''
    return hashlib.sha256('\n'.join(normalized).encode('utf-8')).hexdigest()


def _load_all():
    try:
        data = json.loads(CATALOG_FILE.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_project_folders(sources):
    key = project_key(sources)
    if not key:
        return []
    values = _load_all().get(key, [])
    return sorted({str(name).strip() for name in values if str(name).strip()})


def save_project_folders(sources, names):
    key = project_key(sources)
    if not key:
        return []
    data = _load_all()
    clean = sorted({str(name).strip() for name in names if str(name).strip()})
    if clean:
        data[key] = clean
    else:
        data.pop(key, None)
    CATALOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return clean


def add_project_folder(sources, name):
    names = set(load_project_folders(sources))
    names.add(name)
    return save_project_folders(sources, names)


def rename_project_folder(sources, old, new):
    names = set(load_project_folders(sources))
    names.discard(old)
    names.add(new)
    return save_project_folders(sources, names)
