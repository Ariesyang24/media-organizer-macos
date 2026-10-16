"""Contiguous product grouping and non-destructive local preview generation."""
from __future__ import annotations

import csv
import hashlib
import html
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
IGNORED_DIRECTORY_NAMES = {"智能分款预览", "_预览", ".media-organizer"}

@dataclass(frozen=True)
class GroupedItem:
    source: Path
    group_index: int
    thumbnail: Path

@dataclass(frozen=True)
class GroupingResult:
    root: Path
    output_dir: Path
    html_path: Path
    csv_path: Path
    items: tuple[GroupedItem, ...]
    boundaries: tuple[int, ...]
    @property
    def group_counts(self) -> tuple[int, ...]:
        if not self.items:
            return ()
        count = max(item.group_index for item in self.items)
        return tuple(sum(item.group_index == i for item in self.items) for i in range(1, count + 1))

def _natural_key(path: Path) -> tuple:
    numbers = tuple(int(value) for value in re.findall(r"\d+", path.stem))
    try:
        modified = path.stat().st_mtime
    except OSError:
        modified = 0.0
    return (modified, numbers, path.name.casefold())

def collect_media(root: os.PathLike[str] | str) -> list[Path]:
    base = Path(root).resolve()
    files = []
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in MEDIA_EXTENSIONS:
            continue
        if any(part in IGNORED_DIRECTORY_NAMES for part in path.relative_to(base).parts[:-1]):
            continue
        files.append(path)
    files.sort(key=_natural_key)
    return files

def _read_image(cv2, np, path: Path):
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None

def _frame(cv2, np, path: Path):
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        return _read_image(cv2, np, path)
    capture = cv2.VideoCapture(str(path))
    try:
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if total > 1:
            capture.set(cv2.CAP_PROP_POS_FRAMES, min(total - 1, int(total * .28)))
        ok, value = capture.read()
        return value if ok else None
    finally:
        capture.release()

def _descriptor(cv2, np, frame):
    frame = cv2.resize(frame, (128, 128), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    histogram = cv2.calcHist([hsv], [0, 1], None, [18, 8], [0, 180, 0, 256]).reshape(-1)
    histogram /= np.linalg.norm(histogram) + 1e-8
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    small = cv2.resize(cv2.GaussianBlur(lab, (7, 7), 0), (16, 16), interpolation=cv2.INTER_AREA)
    return np.concatenate([histogram * 1.4, small.astype("float32").reshape(-1) / 255.0])

def _distance(np, left, right) -> float:
    cosine = 1.0 - float(np.dot(left, right) / ((np.linalg.norm(left) * np.linalg.norm(right)) + 1e-8))
    return cosine + float(np.mean(np.abs(left - right)))

def _boundaries(np, descriptors, groups: int) -> tuple[int, ...]:
    count = len(descriptors)
    if groups <= 1:
        return ()
    window = min(4, max(2, count // max(8, groups * 3)))
    minimum = max(2, count // max(12, groups * 5))
    candidates = []
    for index in range(minimum, count - minimum + 1):
        left = np.mean(descriptors[max(0, index-window):index], axis=0)
        right = np.mean(descriptors[index:min(count, index+window)], axis=0)
        candidates.append((_distance(np, left, right), index))
    chosen = []
    for _score, index in sorted(candidates, reverse=True):
        trial = sorted(chosen + [index]); edges = [0, *trial, count]
        if all(edges[i+1] - edges[i] >= minimum for i in range(len(edges)-1)):
            chosen.append(index)
            if len(chosen) == groups - 1:
                break
    if len(chosen) < groups - 1:
        chosen = [round(count * i / groups) for i in range(1, groups)]
    return tuple(sorted(chosen))

def _thumbnail(cv2, frame, target: Path) -> None:
    height, width = frame.shape[:2]
    scale = min(360/max(width, 1), 240/max(height, 1), 1.0)
    resized = cv2.resize(frame, (max(1, int(width*scale)), max(1, int(height*scale))), interpolation=cv2.INTER_AREA)
    ok, encoded = cv2.imencode(".jpg", resized, [int(cv2.IMWRITE_JPEG_QUALITY), 84])
    if not ok:
        raise RuntimeError("无法生成缩略图")
    encoded.tofile(str(target))

def generate_product_style_preview(root, group_count=2, progress: Callable[[int,int,str],None] | None = None) -> GroupingResult:
    import cv2
    import numpy as np
    base = Path(root).resolve(); media = collect_media(base)
    if len(media) < 2:
        raise ValueError("至少需要 2 个照片或视频素材")
    group_count = max(1, min(int(group_count), min(12, len(media))))
    output = base / "智能分款预览"; thumbs = output / "缩略图"; thumbs.mkdir(parents=True, exist_ok=True)
    usable = []
    for position, path in enumerate(media, 1):
        if progress: progress(position, len(media), path.name)
        frame = _frame(cv2, np, path)
        if frame is None: continue
        digest = hashlib.sha1(str(path).encode("utf-8", "ignore")).hexdigest()[:10]
        target = thumbs / f"{path.stem[:48]}-{digest}.jpg"
        _thumbnail(cv2, frame, target)
        usable.append((path, _descriptor(cv2, np, frame), target))
    if len(usable) < group_count:
        raise ValueError("可以读取的素材数量不足，无法完成分组")
    cuts = _boundaries(np, np.stack([entry[1] for entry in usable]), group_count)
    items = tuple(GroupedItem(path, 1 + sum(index >= cut for cut in cuts), thumb) for index, (path, _value, thumb) in enumerate(usable))
    csv_path = output / "分款清单.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle); writer.writerow(["分组", "文件名", "原始路径"])
        for item in items: writer.writerow([f"款式{item.group_index:02d}", item.source.name, str(item.source)])
    sections = []
    for group in range(1, group_count+1):
        cards = []
        for item in (x for x in items if x.group_index == group):
            cards.append(f'<a class="card" href="{html.escape(item.source.as_uri())}"><img loading="lazy" src="{html.escape(item.thumbnail.relative_to(output).as_posix())}"><span title="{html.escape(str(item.source))}">{html.escape(item.source.name)}</span></a>')
        sections.append(f'<section><h2>款式 {group:02d} <small>{len(cards)} 项</small></h2><div class="grid">{"".join(cards)}</div></section>')
    html_path = output / "素材预览.html"
    html_path.write_text("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>智能分款预览</title><style>body{font-family:Segoe UI,Microsoft YaHei,sans-serif;margin:0;background:#eef1f6;color:#16213e}header{position:sticky;top:0;padding:20px 28px;background:#26365f;color:white}main{padding:12px 28px 40px}section{background:white;border:1px solid #dce2ec;border-radius:14px;padding:18px;margin:16px 0}h2{margin:0 0 14px}small{color:#6f7685;font-size:14px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px}.card{color:inherit;text-decoration:none;border:1px solid #e2e7ef;border-radius:10px;overflow:hidden;background:white}.card:hover{border-color:#3f63d7;box-shadow:0 6px 18px #26365f22}.card img{width:100%;height:150px;object-fit:contain;background:#15171d}.card span{display:block;padding:9px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}</style>" + f"<header><strong>智能分款预览</strong> · {len(items)} 项素材 · {group_count} 款</header><main>{''.join(sections)}</main></html>", encoding="utf-8")
    return GroupingResult(base, output, html_path, csv_path, items, cuts)

def move_grouped_media(result: GroupingResult) -> tuple[Path, ...]:
    destinations = []
    replacements = []
    for item in result.items:
        folder = result.root / f"{item.group_index:02d}_款式"; folder.mkdir(exist_ok=True)
        target = folder / item.source.name; serial = 2
        while target.exists() and target.resolve() != item.source.resolve():
            target = folder / f"{item.source.stem}_{serial}{item.source.suffix}"; serial += 1
        if item.source.resolve() != target.resolve(): shutil.move(str(item.source), str(target))
        destinations.append(target)
        replacements.append((item, target))
    # Keep both deliverables useful after files have moved.  Thumbnail paths do
    # not change; only the clickable original-media links and CSV paths do.
    if result.html_path.exists():
        page = result.html_path.read_text(encoding="utf-8")
        for item, target in replacements:
            page = page.replace(html.escape(item.source.as_uri()), html.escape(target.as_uri()))
        result.html_path.write_text(page, encoding="utf-8")
    with result.csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle); writer.writerow(["分组", "文件名", "整理后路径"])
        for item, target in replacements:
            writer.writerow([f"款式{item.group_index:02d}", target.name, str(target)])
    return tuple(destinations)
