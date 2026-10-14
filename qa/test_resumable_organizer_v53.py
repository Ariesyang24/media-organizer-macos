import json
import sys
import tempfile
import threading
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from resumable_organizer import ResumableOrganizer


def make_rows(source):
    return [
        {
            "p": path,
            "target": "2026.10.13 测试",
            "date": "2026-10-13",
            "dev": "测试设备",
            "place": "",
        }
        for path in sorted(source.iterdir())
    ]


with tempfile.TemporaryDirectory(prefix="media-organizer-v53-") as temp:
    root = Path(temp)
    source = root / "source"
    output = root / "output"
    source.mkdir()
    output.mkdir()
    for index in range(3):
        (source / f"sample-{index}.jpg").write_bytes(bytes([index + 1]) * (1024 + index))

    rows = make_rows(source)
    stop = threading.Event()
    first_progress = []

    def stop_after_first(number, total, counts, name):
        first_progress.append((number, dict(counts), name))
        if number == 1:
            stop.set()

    runner = ResumableOrganizer(output)
    first_counts, _ = runner.execute(rows, copy_mode=True, stop_event=stop, progress=stop_after_first)
    runner.close()

    stop.clear()
    runner = ResumableOrganizer(output)
    second_counts, second_report = runner.execute(
        rows, copy_mode=True, stop_event=stop,
        progress=lambda *_args: None,
    )
    remaining, recognized = runner.estimate_remaining(rows)

    missing = {
        "p": source / "missing.jpg",
        "target": "2026.10.13 测试",
        "date": "2026-10-13",
        "dev": "测试设备",
        "place": "",
    }
    failed_counts, failed_report = runner.execute(
        [missing], copy_mode=True, stop_event=stop,
        progress=lambda *_args: None,
    )
    runner.close()

    copied = sorted((output / "2026.10.13 测试").glob("*.jpg"))
    results = {
        "first_run_stopped_safely": first_counts == {"completed": 1, "skipped": 0, "failed": 0, "pending": 2},
        "resume_skipped_completed": second_counts == {"completed": 2, "skipped": 1, "failed": 0, "pending": 0},
        "all_outputs_present": len(copied) == 3,
        "estimate_recognizes_all": remaining == 0 and recognized == 3,
        "missing_source_recorded_as_failure": failed_counts["failed"] == 1 and "failed:" in failed_report[0][3],
        "source_files_preserved": len(list(source.glob("*.jpg"))) == 3,
    }
    print(json.dumps(results, ensure_ascii=False, indent=2))
    assert all(results.values())
