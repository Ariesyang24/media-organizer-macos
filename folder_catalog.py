import json
from pathlib import Path


CATALOG_FILE = Path(__file__).resolve().parent / 'test-results' / 'custom-folder-catalog.json'


def load_folder_catalog():
    try:
        data = json.loads(CATALOG_FILE.read_text(encoding='utf-8'))
        return sorted({str(name).strip() for name in data if str(name).strip()})
    except Exception:
        return []


def save_folder_catalog(names):
    clean = sorted({str(name).strip() for name in names if str(name).strip()})
    CATALOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_FILE.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding='utf-8')
    return clean


def add_folder_to_catalog(name):
    names = set(load_folder_catalog()); names.add(name)
    return save_folder_catalog(names)


def rename_folder_in_catalog(old, new):
    names = set(load_folder_catalog()); names.discard(old); names.add(new)
    return save_folder_catalog(names)
