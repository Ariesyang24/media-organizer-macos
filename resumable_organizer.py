"""Memory-bounded, resumable execution for the final organize step."""

from __future__ import annotations

import csv
import hashlib
import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _copy_with_hash(source: Path, destination: Path) -> str:
    """Copy in one bounded-memory pass while calculating the source checksum."""
    digest = hashlib.sha256()
    with source.open('rb') as reader, destination.open('xb') as writer:
        for block in iter(lambda: reader.read(4 * 1024 * 1024), b''):
            digest.update(block)
            writer.write(block)
        writer.flush()
        os.fsync(writer.fileno())
    shutil.copystat(source, destination)
    return digest.hexdigest()


def _task_key(source: Path, requested: Path, size: int, mtime_ns: int) -> str:
    value = f"{source.resolve()}\0{requested.resolve()}\0{size}\0{mtime_ns}"
    return hashlib.sha256(value.encode("utf-8", "surrogatepass")).hexdigest()


class ResumableOrganizer:
    """Executes one file at a time and commits progress after every file."""

    def __init__(self, output: Path):
        self.output = Path(output)
        state_dir = self.output / ".media-organizer"
        state_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = state_dir / "organize-state.sqlite3"
        self.db = sqlite3.connect(self.db_path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                task_key TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                source_size INTEGER NOT NULL,
                source_mtime_ns INTEGER NOT NULL,
                checksum TEXT,
                status TEXT NOT NULL,
                error TEXT,
                updated_at TEXT NOT NULL
            )"""
        )
        self.db.commit()

    def close(self):
        self.db.close()

    def _saved(self, key: str):
        return self.db.execute(
            "SELECT destination, checksum, status FROM tasks WHERE task_key=?", (key,)
        ).fetchone()

    def estimate_remaining(self, rows):
        """Return (remaining bytes, recognized completed count) without loading files."""
        remaining = 0
        completed = 0
        for row in rows:
            source = Path(row["p"])
            try:
                stat = source.stat()
            except OSError:
                continue
            saved = self.db.execute(
                """SELECT destination FROM tasks
                   WHERE source=? AND source_size=? AND source_mtime_ns=?
                     AND status='completed'
                   ORDER BY updated_at DESC LIMIT 1""",
                (str(source), stat.st_size, stat.st_mtime_ns),
            ).fetchone()
            if saved:
                destination = Path(saved[0])
                try:
                    if destination.is_file() and destination.stat().st_size == stat.st_size:
                        completed += 1
                        continue
                except OSError:
                    pass
            remaining += stat.st_size
        return remaining, completed

    def _record(self, key, source, destination, size, mtime_ns, checksum, status, error=""):
        self.db.execute(
            """INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(task_key) DO UPDATE SET
                 destination=excluded.destination, checksum=excluded.checksum,
                 status=excluded.status, error=excluded.error,
                 updated_at=excluded.updated_at""",
            (key, str(source), str(destination), size, mtime_ns, checksum,
             status, error, datetime.now().isoformat(timespec="seconds")),
        )
        self.db.commit()

    @staticmethod
    def _verified(destination: Path, size: int, checksum: str | None) -> bool:
        if not checksum or not destination.is_file():
            return False
        try:
            return destination.stat().st_size == size and _sha256(destination) == checksum
        except OSError:
            return False

    @staticmethod
    def _checkpoint_matches(destination: Path, size: int, mtime_ns: int,
                            checksum: str | None) -> bool:
        """Fast resume check; copy2 preserves size and modification time."""
        if not checksum or not destination.is_file():
            return False
        try:
            stat = destination.stat()
            return stat.st_size == size and abs(stat.st_mtime_ns - mtime_ns) <= 2_000_000_000
        except OSError:
            return False

    def execute(self, rows, *, copy_mode: bool, stop_event, progress):
        total = len(rows)
        counts = {"completed": 0, "skipped": 0, "failed": 0, "pending": total}
        report_rows = []

        for index, row in enumerate(rows, 1):
            if stop_event.is_set():
                break
            source = Path(row["p"])
            requested = self.output / row["target"] / row.get("output_name", source.name)
            destination = requested
            try:
                stat = source.stat()
                key = _task_key(source, requested, stat.st_size, stat.st_mtime_ns)
                saved = self._saved(key)
                if saved:
                    destination = Path(saved[0])
                    if saved[2] == "completed" and self._checkpoint_matches(
                            destination, stat.st_size, stat.st_mtime_ns, saved[1]):
                        counts["skipped"] += 1
                        counts["pending"] -= 1
                        report_rows.append((row, destination, saved[1], "already-completed"))
                        progress(index, total, counts, source.name)
                        continue

                checksum = saved[1] if saved and saved[1] else None
                suffix = 2
                if destination.exists() and not checksum:
                    checksum = _sha256(source)
                while destination.exists() and _sha256(destination) != checksum:
                    destination = requested.with_name(
                        f"{requested.stem}_{suffix}{requested.suffix}"
                    )
                    suffix += 1
                destination.parent.mkdir(parents=True, exist_ok=True)
                self._record(key, source, destination, stat.st_size, stat.st_mtime_ns,
                             checksum, "running")

                if checksum and destination.exists() and self._verified(destination, stat.st_size, checksum):
                    pass
                elif copy_mode:
                    partial = destination.with_name(
                        f".{destination.name}.partial-{uuid.uuid4().hex}"
                    )
                    try:
                        copied_checksum = _copy_with_hash(source, partial)
                        checksum = checksum or copied_checksum
                        if copied_checksum != checksum or partial.stat().st_size != stat.st_size:
                            raise IOError("复制后校验失败")
                        os.replace(partial, destination)
                    finally:
                        try:
                            partial.unlink(missing_ok=True)
                        except OSError:
                            pass
                else:
                    checksum = checksum or _sha256(source)
                    shutil.move(str(source), str(destination))
                    if not self._verified(destination, stat.st_size, checksum):
                        raise IOError("移动后 SHA-256 校验失败")

                self._record(key, source, destination, stat.st_size, stat.st_mtime_ns,
                             checksum, "completed")
                counts["completed"] += 1
                counts["pending"] -= 1
                report_rows.append((row, destination, checksum, "completed"))
            except Exception as exc:
                counts["failed"] += 1
                counts["pending"] -= 1
                try:
                    stat = source.stat()
                    key = _task_key(source, requested, stat.st_size, stat.st_mtime_ns)
                    self._record(key, source, destination, stat.st_size, stat.st_mtime_ns,
                                 None, "failed", str(exc))
                except OSError:
                    pass
                report_rows.append((row, destination, "", f"failed: {exc}"))
            progress(index, total, counts, source.name)

        counts["pending"] = total - counts["completed"] - counts["skipped"] - counts["failed"]
        return counts, report_rows


def write_report(output: Path, report_rows):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(output) / f"整理记录_{stamp}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow([
            "FileName", "OutputFileName", "OriginalPath", "CaptureDate",
            "Device", "Location", "TargetPath", "SHA256", "Status",
        ])
        for row, destination, checksum, status in report_rows:
            writer.writerow([
                Path(row["p"]).name, destination.name, row["p"], row.get("date", ""),
                row.get("dev", ""), row.get("place", ""), destination, checksum, status,
            ])
    return path
