import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v3_ui_components import CanvasButton
LAUNCHER = ROOT / "launch_media_organizer_safe_drag_v53.pyw"
SOURCE = LAUNCHER.read_text(encoding="utf-8-sig").rsplit(
    "if __name__ == '__main__':", 1
)[0]
SCOPE = {"__name__": "v53_test", "__file__": str(LAUNCHER)}
exec(compile(SOURCE, str(LAUNCHER), "exec"), SCOPE)
App = SCOPE["SafeDragV53MediaOrganizerApp"]


def descendants(widget):
    yield widget
    for child in widget.winfo_children():
        yield from descendants(child)


def button(app, text):
    matches = [
        item for item in descendants(app)
        if isinstance(item, CanvasButton) and item.cget("text") == text
    ]
    if not matches:
        raise AssertionError(f"button not found: {text}")
    return matches[-1]


def managed(widget):
    current = widget
    while current is not app:
        if not current.winfo_manager():
            return False
        current = current.master
    return True


def managed_button_texts(app):
    return {
        item.cget("text") for item in descendants(app)
        if isinstance(item, CanvasButton) and managed(item)
    }


app = App()
app.withdraw()
app.update_idletasks()

sample_files = sorted((ROOT / "test-results" / "full-flow-input").iterdir())
photo = next(path for path in sample_files if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
video = next(path for path in sample_files if path.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv"})


def row(path, kind, status="待确认"):
    return {
        "p": path,
        "kind": kind,
        "date": "2026-05-20",
        "place": "未设置",
        "dev": "测试设备",
        "target": "2026.05.20",
        "ts": path.stat().st_mtime,
        "people": set(),
        "people_text": "无人脸",
        "video_analysis": {},
        "custom_folder": "",
        "duplicate": "group-1",
        "burst": "",
        "analysis": {"valid": True, "blur": 80, "exposure": "正常", "quality": 85},
        "recommend": "正常",
        "audit_status": status,
        "audit_result": "画质正常",
        "audit_confidence": 90,
        "audit_reason": "自动测试",
    }


results = {}
try:
    app.rows = [row(photo, "照片"), row(video, "视频")]
    app.scan_busy = False
    app.render()
    app.update_idletasks()

    all_buttons = [item for item in descendants(app) if isinstance(item, CanvasButton)]
    empty_commands = [item.cget("text") or item.cget("icon") for item in all_buttons if item.cget("command") is None]
    results["all_visible_buttons_have_callbacks"] = not empty_commands
    results["empty_callback_buttons"] = empty_commands

    before = int(app.sidebar_v3.cget("width"))
    app._toggle_sidebar(); app.update_idletasks()
    collapsed = int(app.sidebar_v3.cget("width"))
    app._toggle_sidebar(); app.update_idletasks()
    restored = int(app.sidebar_v3.cget("width"))
    results["sidebar_widths"] = [before, collapsed, restored]
    results["sidebar_toggle"] = before in (72, 220) and collapsed != before and restored == before

    drawer = app.embedded_workspace_drawer_v51
    drawer.open_drawer("识别设置"); app.update_idletasks()
    settings_text = {item.cget("text") for item in descendants(drawer.drawer) if isinstance(item, CanvasButton)}
    required_settings = {"取消", "保存设置", "宽松", "标准", "严格", "模特分类管理", "导出审核报告", "表格列设置", "恢复默认设置"}
    results["settings_drawer"] = drawer.kind == "识别设置" and required_settings <= settings_text
    results["settings_drawer_width"] = drawer.drawer.winfo_width()
    drawer.close_drawer(); app.update_idletasks()

    app.tree.selection_set("0")
    app.workspace_interaction_v50.last_selection = [0]
    drawer.open_drawer("批量操作"); app.update_idletasks()
    button(app, "待确认").invoke()
    button(app, "应用调整").invoke()
    app.update_idletasks()
    results["batch_apply"] = app.rows[0].get("manual_audit") == "待确认"
    results["batch_undo_available"] = bool(app.unified_workspace.undo_stack)
    app.unified_workspace.undo(); app.update_idletasks()
    results["batch_undo"] = app.rows[0].get("manual_audit") in (None, "")
    drawer.close_drawer(); app.update_idletasks()

    app.tree.selection_set("0")
    app.workspace_interaction_v50.last_selection = [0]
    drawer.open_drawer("素材详情"); app.update_idletasks()
    labels = {item.cget("text") for item in descendants(drawer.drawer) if item.winfo_class() == "Label"}
    results["details_drawer"] = "素材详情" in labels and photo.name in labels
    drawer.close_drawer(); app.update_idletasks()

    opened = []
    SCOPE["os"].startfile = lambda path: opened.append(Path(path).name)
    app._open_media_row(app.rows[0]); app._open_media_row(app.rows[1])
    results["open_photo_and_video"] = opened == [photo.name, video.name]
    app.tree.selection_set("0"); app.open_original()
    app.rows[1]["video_analysis"] = {"keyframes": [photo]}
    app.tree.selection_set("1"); app.open_keyframes()
    results["drawer_open_original"] = photo.name in opened
    results["drawer_open_keyframes"] = photo.parent.name in opened

    popup_items = []
    original_popup = app._popup_actions
    app._popup_actions = lambda items, *_args: popup_items.extend(item[0] for item in items)
    app.page_state.show_more()
    app._popup_actions = original_popup
    expected_more = ["智能审核", "相似项分组", "移动到分类", "识别设置", "导出审核报告", "列设置"]
    results["more_menu_items"] = popup_items
    results["more_menu_matches_requirement"] = popup_items[:6] == expected_more

    responsive = {}
    app.sidebar_manual_override = False
    screen_width = app.winfo_screenwidth()
    for width, height in ((1280, 720), (1536, 864), (1920, 1080)):
        if width > screen_width:
            responsive[str(width)] = {"skipped": f"screen width is {screen_width}"}
            continue
        app.geometry(f"{width}x{height}")
        app.update_idletasks(); app.page_state.adapt(); app.update_idletasks()
        if app.winfo_width() != width:
            responsive[str(width)] = {"skipped": f"window manager kept width {app.winfo_width()}"}
            continue
        content_children = app.waiting_v38.content.pack_slaves()
        responsive[str(width)] = {
            "window_width": app.winfo_width(),
            "sidebar_width": int(app.sidebar_v3.cget("width")),
            "left_width": int(content_children[0].cget("width")) if content_children else 0,
            "columns": list(app.tree.cget("displaycolumns")),
        }
    results["responsive"] = responsive
    results["responsive_breakpoints"] = responsive["1280"]["sidebar_width"] == 72 and responsive["1280"]["left_width"] == 240
    if "skipped" not in responsive["1536"]:
        results["responsive_breakpoints"] &= responsive["1536"]["sidebar_width"] == 220 and responsive["1536"]["left_width"] == 260
    if "skipped" not in responsive["1920"]:
        results["responsive_breakpoints"] &= responsive["1920"]["sidebar_width"] == 220 and responsive["1920"]["left_width"] == 300

    state_results = {}
    for state in ("WAITING", "SCANNING", "PAUSED", "COMPLETED", "FAILED"):
        app.page_state.apply(state)
        app.update_idletasks()
        texts = managed_button_texts(app)
        state_results[state] = sorted(texts)
    results["states"] = state_results
    results["state_button_rules"] = (
        "扫描并预览" in state_results["WAITING"]
        and "暂停扫描" in state_results["SCANNING"] and "停止扫描" in state_results["SCANNING"]
        and "继续扫描" in state_results["PAUSED"] and "停止扫描" in state_results["PAUSED"]
        and "暂停扫描" not in state_results["PAUSED"]
        and "重新扫描" in state_results["COMPLETED"]
        and not ({"暂停扫描", "继续扫描", "停止扫描"} & set(state_results["COMPLETED"]))
        and {"查看详情", "重新扫描", "返回选择"} <= set(state_results["FAILED"])
    )
finally:
    app.destroy()

print(json.dumps(results, ensure_ascii=False, indent=2))
assert results["sidebar_toggle"]
assert results["settings_drawer"]
assert results["batch_apply"]
assert results["batch_undo"]
assert results["details_drawer"]
assert results["open_photo_and_video"]
assert results["drawer_open_original"]
assert results["drawer_open_keyframes"]
assert results["state_button_rules"]
assert results["responsive_breakpoints"]
