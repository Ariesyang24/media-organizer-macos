import hashlib
import os
import threading
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk


CACHE_ROOT = Path(__file__).resolve().parent / 'test-results' / 'thumbnail-cache'


def _cache_path(path):
    path = Path(path)
    stat = path.stat()
    key = hashlib.sha1(f'{path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}'.encode('utf-8')).hexdigest()
    return CACHE_ROOT / f'{key}.jpg'


def _placeholder(text, size=(240, 150)):
    image = Image.new('RGB', size, '#e9edf2')
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, size[0] - 1, size[1] - 1), outline='#b8c0ca')
    draw.text((12, size[1] // 2 - 8), text, fill='#59636e')
    return image


def _video_frame(path):
    capture = cv2.VideoCapture(str(path))
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if total > 0:
        capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(total * 0.25)))
    ok, frame = capture.read()
    capture.release()
    if not ok:
        return None
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def make_thumbnail(row, size=(240, 150)):
    source = Path(row['p'])
    target = _cache_path(source)
    if target.exists():
        return target
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        if row.get('kind') == '视频':
            frames = row.get('video_analysis', {}).get('keyframes', [])
            if frames and Path(frames[0]).exists():
                image = Image.open(frames[0]).convert('RGB')
            else:
                image = _video_frame(source)
            if image is None:
                image = _placeholder('视频无预览')
        else:
            image = ImageOps.exif_transpose(Image.open(source)).convert('RGB')
        image.thumbnail(size, Image.Resampling.LANCZOS)
        canvas = Image.new('RGB', size, '#15181c')
        canvas.paste(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
        canvas.save(target, 'JPEG', quality=82, optimize=True)
    except Exception:
        _placeholder('无法生成缩略图', size).save(target, 'JPEG', quality=82)
    return target


class ThumbnailGallery:
    def __init__(self, app, title, rows):
        self.app = app
        self.rows = list(rows)
        self.images = []
        self.closed = False
        self.window = app.tk.call('toplevel', app._w + '.gallery') if False else None
        self.window = __import__('tkinter').Toplevel(app)
        self.window.title(f'{title} · {len(self.rows)} 个素材')
        self.window.geometry('1120x760')
        self.window.minsize(760, 520)
        self.window.protocol('WM_DELETE_WINDOW', self.close)

        tk = __import__('tkinter')
        ttk = __import__('tkinter.ttk', fromlist=['ttk'])
        header = ttk.Frame(self.window, padding=12)
        header.pack(fill='x')
        ttk.Label(header, text=title, font=('Segoe UI', 16, 'bold')).pack(side='left')
        self.state = tk.StringVar(value=f'正在准备缩略图… 0/{len(self.rows)}')
        ttk.Label(header, textvariable=self.state, foreground='#666').pack(side='left', padx=14)
        ttk.Button(header, text='关闭', command=self.close).pack(side='right')

        body = ttk.Frame(self.window)
        body.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(body, highlightthickness=0, background='#f5f6f7')
        scrollbar = ttk.Scrollbar(body, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.grid = ttk.Frame(self.canvas, padding=10)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid, anchor='nw')
        self.grid.bind('<Configure>', lambda event: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda event: self.canvas.itemconfigure(self.canvas_window, width=event.width))
        self.canvas.bind_all('<MouseWheel>', self._wheel)
        for column in range(4):
            self.grid.columnconfigure(column, weight=1)

        threading.Thread(target=self._prepare, daemon=True).start()

    def _wheel(self, event):
        if not self.closed:
            self.canvas.yview_scroll(int(-event.delta / 120), 'units')

    def _prepare(self):
        for index, row in enumerate(self.rows):
            if self.closed:
                return
            path = make_thumbnail(row)
            self.app.after(0, lambda i=index, r=row, p=path: self._add_card(i, r, p))

    def _add_card(self, index, row, thumb_path):
        if self.closed or not self.window.winfo_exists():
            return
        ttk = __import__('tkinter.ttk', fromlist=['ttk'])
        image = ImageTk.PhotoImage(Image.open(thumb_path))
        self.images.append(image)
        card = ttk.Frame(self.grid, padding=5, relief='ridge')
        card.grid(row=index // 4, column=index % 4, sticky='nsew', padx=5, pady=5)
        button = ttk.Button(card, image=image, command=lambda path=row['p']: os.startfile(str(path)))
        button.pack(fill='both', expand=True)
        name = row['p'].name
        if len(name) > 30:
            name = name[:27] + '…'
        ttk.Label(card, text=name, anchor='center').pack(fill='x', pady=(5, 0))
        detail = row.get('scene', {}).get('group') or row.get('kind', '')
        ttk.Label(card, text=detail, foreground='#66717c', anchor='center').pack(fill='x')
        done = index + 1
        self.state.set(f'已加载 {done}/{len(self.rows)} · 点击缩略图查看原始高清素材')

    def close(self):
        self.closed = True
        try:
            self.canvas.unbind_all('<MouseWheel>')
            self.window.destroy()
        except Exception:
            pass

