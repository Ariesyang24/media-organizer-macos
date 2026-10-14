import json
from pathlib import Path


OVERRIDES_FILE = Path(__file__).resolve().parent / 'test-results' / 'folder-path-overrides.json'


def load_path_overrides():
    try: return json.loads(OVERRIDES_FILE.read_text(encoding='utf-8'))
    except Exception: return {}


def save_path_overrides(data):
    clean = {str(key): str(value) for key, value in data.items() if str(value).strip()}
    OVERRIDES_FILE.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDES_FILE.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding='utf-8')


def apply_path_overrides(rows):
    data = load_path_overrides()
    for row in rows:
        target = data.get(str(row.get('p', '')))
        if target: row['target'] = target


def rename_target_for_rows(rows, old_target, new_target):
    data = load_path_overrides()
    changed = 0
    for row in rows:
        if row.get('target') == old_target:
            data[str(row['p'])] = str(new_target); changed += 1
    save_path_overrides(data)
    return changed


def clear_path_overrides(rows):
    data = load_path_overrides()
    for row in rows: data.pop(str(row.get('p', '')), None)
    save_path_overrides(data)
