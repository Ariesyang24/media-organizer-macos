import sys
from pathlib import Path

from PIL import ImageGrab


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LAUNCHER = ROOT / "launch_media_organizer_safe_drag_v53.pyw"
SOURCE = LAUNCHER.read_text(encoding="utf-8-sig").rsplit("if __name__ == '__main__':", 1)[0]
SCOPE = {"__name__": "v53_capture", "__file__": str(LAUNCHER)}
exec(compile(SOURCE, str(LAUNCHER), "exec"), SCOPE)
App = SCOPE["SafeDragV53MediaOrganizerApp"]

samples = sorted((ROOT / "test-results" / "full-flow-input").iterdir())
photo = next(path for path in samples if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
video = next(path for path in samples if path.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv"})


def row(path, kind, status, result, confidence):
    return {
        "p": path, "kind": kind, "date": "2026-05-20", "place": "",
        "dev": "测试设备", "target": "2026.05.20", "ts": path.stat().st_mtime,
        "people": set(), "people_text": "无人脸", "video_analysis": {},
        "custom_folder": "", "duplicate": "", "burst": "",
        "analysis": {"valid": True, "blur": 80, "exposure": "正常", "quality": 85},
        "recommend": "正常", "audit_status": status, "audit_result": result,
        "audit_confidence": confidence, "audit_reason": "界面检查样本",
    }


app = App()
app.tk.call("tk", "scaling", 1.0)
app.geometry("1280x720+20+20")
app.attributes("-topmost", True)
app.rows = [
    row(photo, "照片", "自动通过", "白底正常", 96),
    row(video, "视频", "待确认", "主体偏亮", 68),
]
app.scan_busy = False
app.render()
app.page_state.apply("COMPLETED")
app.deiconify(); app.lift(); app.focus_force(); app.update(); app.after(800); app.update()

output = ROOT / "test-results" / "ui-audit"
output.mkdir(parents=True, exist_ok=True)


def capture(name):
    app.update_idletasks(); app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    width, height = app.winfo_width(), app.winfo_height()
    screen = ImageGrab.grab(all_screens=True)
    scale = screen.width / app.winfo_screenwidth()
    image = screen.crop((
        round(x * scale), round(y * scale),
        round((x + width) * scale), round((y + height) * scale),
    ))
    image.resize((width, height)).save(output / name)


capture("completed-1280-closed.png")
app.embedded_workspace_drawer_v51.open_drawer("识别设置")
app.update(); app.after(500); app.update()
print({
    "window": (app.winfo_width(), app.winfo_height()),
    "root": (app.v3_recognition_root.winfo_width(), app.v3_recognition_root.winfo_height()),
    "drawer": (
        app.embedded_workspace_drawer_v51.drawer.winfo_x(),
        app.embedded_workspace_drawer_v51.drawer.winfo_width(),
    ),
})
capture("completed-1280-settings.png")
app.destroy()
print(output)
