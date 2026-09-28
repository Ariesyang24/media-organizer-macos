import builtins
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

root = Path(__file__).resolve().parent
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

app_path = root / 'ai_entry_app.pyw'
source = app_path.read_text(encoding='utf-8').rsplit('AIEntryApp().mainloop()', 1)[0]
scope = {'__file__': str(app_path)}
exec(compile(source, str(app_path), 'exec'), scope)
AIEntryApp = scope['AIEntryApp']


def open_cloud_settings(self):
    window = tk.Toplevel(self)
    window.title('配置云端AI')
    window.geometry('610x455')
    window.resizable(False, False)
    window.transient(self)
    window.grab_set()

    if not hasattr(self, 'cloud_provider'):
        self.cloud_provider = tk.StringVar(value='OpenAI 兼容服务')
        self.cloud_url = tk.StringVar(value='https://api.openai.com/v1')
        self.cloud_model = tk.StringVar(value='gpt-4.1-mini')
        self.cloud_key = tk.StringVar()

    shell = ttk.Frame(window, padding=22)
    shell.pack(fill='both', expand=True)
    ttk.Label(shell, text='云端AI配置', font=('Segoe UI', 17, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w')
    ttk.Label(shell, text='配置后才会启用云端识别；未配置时素材不会上传。', foreground='#666').grid(row=1, column=0, columnspan=2, sticky='w', pady=(4, 18))

    fields = (
        ('AI服务', self.cloud_provider),
        ('API地址', self.cloud_url),
        ('模型名称', self.cloud_model),
        ('API密钥', self.cloud_key),
    )
    for row, (label, variable) in enumerate(fields, 2):
        ttk.Label(shell, text=label).grid(row=row, column=0, sticky='w', pady=7)
        if row == 2:
            widget = ttk.Combobox(shell, textvariable=variable, state='readonly', values=['OpenAI 兼容服务'], width=45)
        else:
            widget = ttk.Entry(shell, textvariable=variable, width=48, show='●' if row == 5 else '')
        widget.grid(row=row, column=1, sticky='ew', padx=(15, 0), pady=7)

    ttk.Label(shell, text='密钥只保留在本次运行内存中，不写入配置文件。', foreground='#777').grid(row=6, column=0, columnspan=2, sticky='w', pady=(12, 0))
    shell.columnconfigure(1, weight=1)

    def save():
        if not self.cloud_url.get().strip() or not self.cloud_model.get().strip():
            messagebox.showwarning('配置不完整', '请填写 API 地址和模型名称。', parent=window)
            return
        if not self.cloud_key.get().strip():
            messagebox.showwarning('缺少密钥', '请填写 API 密钥。', parent=window)
            return
        self.ai_mode.set('云端AI')
        self.scene_on.set(False)
        if hasattr(self, 'ai_state_label'):
            self.ai_state_label.configure(text='当前：云端AI · 已配置')
        self.status.set('云端AI已配置；请先用少量素材测试识别结果')
        window.destroy()
        messagebox.showinfo('配置已保留', '云端AI配置已在本次运行中保留。', parent=self)

    buttons = ttk.Frame(shell)
    buttons.grid(row=7, column=0, columnspan=2, sticky='e', pady=(24, 0))
    ttk.Button(buttons, text='取消', command=window.destroy).pack(side='left')
    ttk.Button(buttons, text='保留配置', command=save).pack(side='left', padx=(8, 0))


AIEntryApp.cloud_placeholder = open_cloud_settings
AIEntryApp().mainloop()
