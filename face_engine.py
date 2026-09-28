import json, sqlite3
from pathlib import Path
import cv2, numpy as np
from recognition_engine import decode

ROOT=Path(__file__).resolve().parent
DETECTOR_MODEL=str(ROOT/'tools'/'face_detection_yunet_2026may.onnx')
RECOGNIZER_MODEL=str(ROOT/'tools'/'face_recognition_sface_2021dec.onnx')

class FaceEngine:
    def __init__(self,cache_path):
        self.detector=cv2.FaceDetectorYN.create(DETECTOR_MODEL,'',(320,320),0.8,0.3,5000)
        self.recognizer=cv2.FaceRecognizerSF.create(RECOGNIZER_MODEL,'')
        self.db=sqlite3.connect(cache_path);self.db.execute('create table if not exists faces(path text,mtime real,size integer,idx integer,embedding blob,box text,primary key(path,idx))');self.db.commit()
    def extract(self,path):
        stat=path.stat();cached=self.db.execute('select embedding,box from faces where path=? and mtime=? and size=? order by idx',(str(path),stat.st_mtime,stat.st_size)).fetchall()
        if cached:return [(np.frombuffer(e,dtype=np.float32),json.loads(b)) for e,b in cached]
        image=decode(path)
        if image is None:return []
        h,w=image.shape[:2]; scale=min(1.0,1280/max(h,w)); work=cv2.resize(image,(int(w*scale),int(h*scale))) if scale<1 else image
        self.detector.setInputSize((work.shape[1],work.shape[0]));_,faces=self.detector.detect(work);result=[]
        self.db.execute('delete from faces where path=?',(str(path),))
        for idx,face in enumerate(faces if faces is not None else []):
            try:
                aligned=self.recognizer.alignCrop(work,face);feature=self.recognizer.feature(aligned).flatten().astype(np.float32);feature/=max(np.linalg.norm(feature),1e-8);box=[float(v/scale) for v in face[:4]];result.append((feature,box));self.db.execute('insert or replace into faces values(?,?,?,?,?,?)',(str(path),stat.st_mtime,stat.st_size,idx,feature.tobytes(),json.dumps(box)))
            except Exception:pass
        self.db.commit();return result
    def close(self):self.db.close()

def cluster(rows,threshold=0.42):
    entries=[]
    for ri,row in enumerate(rows):
        for fi,(embedding,box) in enumerate(row.get('faces',[])):entries.append((ri,fi,embedding,box))
    parent=list(range(len(entries)))
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    for i in range(len(entries)):
        for j in range(i+1,len(entries)):
            if float(np.dot(entries[i][2],entries[j][2]))>=threshold:
                a,b=find(i),find(j)
                if a!=b:parent[b]=a
    groups={}
    for i,e in enumerate(entries):groups.setdefault(find(i),[]).append(e)
    ordered=sorted(groups.values(),key=lambda g:(-len({x[0] for x in g}),min(x[0] for x in g)))
    for number,items in enumerate(ordered,1):
        label=f'人物 {number:03d}'
        for ri,_,_,_ in items:rows[ri].setdefault('people',set()).add(label)
    for row in rows:row['people_text']='、'.join(sorted(row.get('people',set()))) or '无人脸'
    return len(entries),len(ordered)
