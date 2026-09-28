from pathlib import Path
namespace={}
source=Path(__file__).with_name('review_workflow_app.pyw').read_text(encoding='utf-8').rsplit('ReviewApp().mainloop()',1)[0]
exec(compile(source,'review_workflow_app.pyw','exec'),namespace)
ReviewApp=namespace['ReviewApp']

class ReviewFixedApp(ReviewApp):
    def apply_filter(self):
        if not hasattr(self,'tree'):return
        shown=0
        for i,row in enumerate(self.rows):
            item=str(i);visible=self.match(row)
            if self.tree.exists(item):
                if visible:self.tree.reattach(item,'','end');shown+=1
                else:self.tree.detach(item)
        self.status.set(f'当前显示 {shown}/{len(self.rows)}；筛选核对后可排除项目或执行整理')

ReviewFixedApp().mainloop()
