import json, sqlite3
from pathlib import Path
import cv2, numpy as np
from recognition_engine import decode

ROOT=Path(__file__).resolve().parent
DETECTOR_MODEL=str(ROOT/'tools'/'face_detection_yunet_2026may.onnx')
RECOGNIZER_MODEL=str(ROOT/'tools'/'face_recognition_sface_2021dec.onnx')
ENGINE_VERSION='2'

class FaceEngine:
    def __init__(self,cache_path):
        self.detector=cv2.FaceDetectorYN.create(DETECTOR_MODEL,'',(320,320),0.65,0.3,5000)
        self.recognizer=cv2.FaceRecognizerSF.create(RECOGNIZER_MODEL,'')
        self.db=sqlite3.connect(cache_path);self.db.execute('create table if not exists faces(path text,mtime real,size integer,idx integer,embedding blob,box text,primary key(path,idx))');self.db.execute('create table if not exists face_meta(key text primary key,value text)');version=self.db.execute("select value from face_meta where key='engine_version'").fetchone();self.db.execute('delete from faces') if not version or version[0]!=ENGINE_VERSION else None;self.db.execute("insert or replace into face_meta values('engine_version',?)",(ENGINE_VERSION,));self.db.commit()
    def extract(self,path):
        stat=path.stat();cached=self.db.execute('select embedding,box from faces where path=? and mtime=? and size=? order by idx',(str(path),stat.st_mtime,stat.st_size)).fetchall()
        if cached:return [(np.frombuffer(e,dtype=np.float32),json.loads(b)) for e,b in cached]
        image=decode(path)
        if image is None:return []
        h,w=image.shape[:2]; scale=min(2.0,1920/max(h,w)); work=cv2.resize(image,(max(1,int(w*scale)),max(1,int(h*scale))),interpolation=cv2.INTER_CUBIC if scale>1 else cv2.INTER_AREA) if abs(scale-1)>0.01 else image
        self.detector.setInputSize((work.shape[1],work.shape[0]));_,faces=self.detector.detect(work);result=[]
        self.db.execute('delete from faces where path=?',(str(path),))
        for idx,face in enumerate(faces if faces is not None else []):
            try:
                aligned=self.recognizer.alignCrop(work,face);feature=self.recognizer.feature(aligned).flatten().astype(np.float32);feature/=max(np.linalg.norm(feature),1e-8);box=[float(v/scale) for v in face[:4]];result.append((feature,box));self.db.execute('insert or replace into faces values(?,?,?,?,?,?)',(str(path),stat.st_mtime,stat.st_size,idx,feature.tobytes(),json.dumps(box)))
            except Exception:pass
        self.db.commit();return result
    def close(self):self.db.close()

def cluster(rows,threshold=0.38):
    entries=[]
    for ri,row in enumerate(rows):
        for fi,(embedding,box) in enumerate(row.get('faces',[])):entries.append((ri,fi,embedding,box))
    groups=[];centroids=[]
    for entry in entries:
        embedding=entry[2];scores=[float(np.dot(embedding,c)) for c in centroids]
        best=int(np.argmax(scores)) if scores else -1
        if best>=0 and scores[best]>=threshold:
            groups[best].append(entry);centroid=np.mean([x[2] for x in groups[best]],axis=0);centroids[best]=centroid/max(np.linalg.norm(centroid),1e-8)
        else:groups.append([entry]);centroids.append(embedding.copy())
    ordered=sorted(groups,key=lambda g:(-len({x[0] for x in g}),min(x[0] for x in g)))
    for number,items in enumerate(ordered,1):
        label=f'人物 {number:03d}'
        for ri,_,_,_ in items:rows[ri].setdefault('people',set()).add(label)
    for row in rows:row['people_text']='、'.join(sorted(row.get('people',set()))) or '无人脸'
    return len(entries),len(ordered)
