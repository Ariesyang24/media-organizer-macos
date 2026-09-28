from media_organizer_windows_v2 import *

class FinalApp(FullApp):
    def calculate(self):
        known={r['p'].parent:r['dev'] for r in self.rows if r['dev']!='未知设备'}; groups={}
        for r in self.rows:
            r['dev']=known.get(r['p'].parent,r['dev']); key=(r['date'].replace('-','.')+' '+self.comp(r['place']),self.comp(r['dev'])); groups.setdefault(key,set()).add(r['p'].parent)
        nums={}
        for key,folders in groups.items():
            if len(folders)>1:
                for i,f in enumerate(sorted(folders),1): nums[key+(f,)]=f'{i:03d}'
        for r in self.rows:
            batch=r['date'].replace('-','.')+' '+self.comp(r['place']); dev=self.comp(r['dev']); kind=('Photos' if r['kind']=='照片' else 'Videos') if self.english.get() else r['kind']; target=Path(batch)/f'{dev} {kind}'; number=nums.get((batch,dev,r['p'].parent))
            if number: target/=number
            r['target']=str(target)
    def render(self):
        self.calculate(); FullApp.render(self)
    def retarget(self):
        self.calculate(); FullApp.render(self)
    def full_run(self,out):
        if self.rename_on.get() and self.rename_base.get().strip():
            groups={}
            for r in self.rows:
                if r['kind']=='照片': groups.setdefault(r['target'],{}).setdefault(r['p'].stem,[]).append(r)
            for target,stems in groups.items():
                ordered=sorted(stems.items(),key=lambda x:(min(v['ts'] for v in x[1]),x[0]))
                for i,(_,items) in enumerate(ordered,1):
                    for r in items:r['output_name']=f'{safe(self.rename_base.get())}_{i:04d}{r["p"].suffix.lower()}'
        done=[]; failed=[]
        for i,r in enumerate(self.rows,1):
            if self.stop.is_set():break
            try:
                folder=out/r['target']; folder.mkdir(parents=True,exist_ok=True); source=r['p']; checksum=sha(source); dst=folder/r.get('output_name',source.name); n=2
                while dst.exists() and sha(dst)!=checksum: dst=folder/f'{dst.stem}_{n}{dst.suffix}';n+=1
                if self.copy_mode.get():
                    if not dst.exists():
                        part=dst.with_name(f'.{dst.name}.partial-{uuid.uuid4().hex}');shutil.copy2(source,part)
                        if sha(part)!=checksum:raise IOError('SHA-256 校验失败')
                        os.replace(part,dst)
                elif not dst.exists(): shutil.move(str(source),str(dst))
                done.append((r,dst,checksum))
            except Exception as e:failed.append(f'{r["p"]}: {e}')
            self.update(i,len(self.rows),f'整理 {i}/{len(self.rows)}：{r["p"].name}')
        stamp=datetime.now().strftime('%Y%m%d_%H%M%S');report=out/f'整理记录_{stamp}.csv'
        with report.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f);w.writerow(['FileName','OutputFileName','OriginalPath','CaptureDate','Device','Location','LocationSource','TargetPath','SHA256','Verification'])
            for r,d,s in done:w.writerow([r['p'].name,d.name,r['p'],datetime.fromtimestamp(r['ts']).isoformat(),r['dev'],r['place'],'手动' if r.get('manual') else '自动',d,s,'verified'])
        if failed:(out/f'整理失败_{stamp}.txt').write_text('\n'.join(failed),encoding='utf-8')
        self.update(len(done),len(self.rows),f'{"已安全停止" if self.stop.is_set() else "整理完成"}：成功 {len(done)}，失败 {len(failed)}；{report}')

if __name__=='__main__': FinalApp().mainloop()
