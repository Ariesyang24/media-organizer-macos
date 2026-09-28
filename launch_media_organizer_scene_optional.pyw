import builtins
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scene-runtime'))
builtins.__file__ = str(root / 'launch_scene_folder_final.pyw')

complete_path = root / 'launch_media_organizer_complete.pyw'
source = complete_path.read_text(encoding='utf-8').rsplit('CompleteMediaOrganizerApp().mainloop()', 1)[0]
scope = {'__file__': str(complete_path)}
exec(compile(source, str(complete_path), 'exec'), scope)
CompleteMediaOrganizerApp = scope['CompleteMediaOrganizerApp']


class SceneOptionalMediaOrganizerApp(CompleteMediaOrganizerApp):
    OFF = '不使用场景识别（推荐）'
    ON = '使用离线场景识别（实验）'

    def __init__(self):
        super().__init__()
        self.scene_choice = tk.StringVar(value=self.OFF)
        self.scene_on.set(False)
        self._replace_scene_toggle()
        self._render_scene_folders()
        self.status.set('场景识别默认关闭；其他识别和缩略图功能正常使用')

    def _replace_scene_toggle(self):
        control_row = self.scene_panel.pack_info().get('after')
        controls = self.scene_panel.master.nametowidget(control_row) if control_row else None
        if controls is None:
            return
        for child in controls.winfo_children():
            if child.winfo_class() == 'TCheckbutton':
                child.pack_forget()
            elif child.winfo_class() == 'TLabel':
                child.configure(text='场景分类对部分素材可能不准，默认不使用')
        ttk.Label(controls, text='场景识别：').pack(side='left', before=controls.winfo_children()[0] if controls.winfo_children() else None)
        selector = ttk.Combobox(
            controls,
            textvariable=self.scene_choice,
            values=(self.OFF, self.ON),
            state='readonly',
            width=30,
        )
        selector.pack(side='left', padx=(4, 12))
        selector.bind('<<ComboboxSelected>>', self._scene_choice_changed)

    def _scene_choice_changed(self, event=None):
        enabled = self.scene_choice.get() == self.ON
        self.scene_on.set(enabled)
        if not enabled:
            for row in self.rows:
                row.pop('scene', None)
            self._render_scene_folders()
            self.status.set('已关闭场景识别；错误的场景分类已隐藏')
        else:
            self._render_scene_folders()
            self.status.set('已选择实验性场景识别；请点击重新扫描生成结果')

    def _render_scene_folders(self):
        if hasattr(self, 'scene_choice') and self.scene_choice.get() == self.OFF:
            for child in self.scene_panel.winfo_children():
                child.destroy()
            ttk.Label(
                self.scene_panel,
                text='已选择“不使用场景识别”。照片、视频、人物和缩略图功能不受影响。',
                foreground='#666',
            ).grid(row=0, column=0, sticky='w', padx=4, pady=4)
            return
        super()._render_scene_folders()

    def _apply_ai_mode(self):
        if self.ai_mode.get() == '本地AI':
            self.scene_on.set(self.scene_choice.get() == self.ON)
            state = '场景识别已开启' if self.scene_on.get() else '场景识别未选择'
            text = f'当前：本地AI · {state}'
        else:
            self.scene_on.set(False)
            text = '当前：云端AI · 等待配置'
        if hasattr(self, 'ai_state_label'):
            self.ai_state_label.configure(text=text)


SceneOptionalMediaOrganizerApp().mainloop()
