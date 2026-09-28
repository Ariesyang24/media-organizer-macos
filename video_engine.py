import hashlib
from pathlib import Path
import cv2, numpy as np
from scenedetect import open_video, SceneManager, ContentDetector

def frame_metrics(frame):
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY);blur=float(cv2.Laplacian(gray,cv2.CV_64F).var());mean=float(gray.mean());dark=float((gray<20).mean());bright=float((gray>245).mean())
    exposure='严重欠曝' if dark>.45 or mean<45 else '严重过曝' if bright>.35 or mean>220 else '轻微欠曝' if mean<75 else '轻微过曝' if mean>190 else '正常'
    hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV);sat=float(hsv[:,:,1].mean());style='暗光' if mean<65 else '明亮' if mean>190 else '高饱和' if sat>130 else '低饱和' if sat<45 else '自然'
    return blur,exposure,style

def analyze_video(path,cache_root,max_scenes=100):
    result={'scenes':0,'duration':0,'keyframes':[],'blur':0,'exposure':'未知','visual':'未知','valid':True}
    try:
        video=open_video(str(path));manager=SceneManager();manager.add_detector(ContentDetector(threshold=27.0,min_scene_len=15));manager.detect_scenes(video,show_progress=False);scenes=manager.get_scene_list(start_in_scene=True)[:max_scenes];result['scenes']=len(scenes);result['duration']=video.duration.get_seconds()
        folder=Path(cache_root)/hashlib.sha1(str(path).encode('utf-8')).hexdigest();folder.mkdir(parents=True,exist_ok=True);cap=cv2.VideoCapture(str(path));metrics=[]
        for index,(start,end) in enumerate(scenes):
            second=(start.get_seconds()+end.get_seconds())/2;cap.set(cv2.CAP_PROP_POS_MSEC,second*1000);ok,frame=cap.read()
            if not ok:continue
            metrics.append(frame_metrics(frame));thumb=folder/f'scene_{index+1:03d}_{second:.2f}s.jpg';cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,88])[1].tofile(str(thumb));result['keyframes'].append(str(thumb))
        cap.release()
        if metrics:
            result['blur']=sum(x[0] for x in metrics)/len(metrics);ex=[x[1] for x in metrics];vis=[x[2] for x in metrics];result['exposure']=max(set(ex),key=ex.count);result['visual']=max(set(vis),key=vis.count)
    except Exception as exc:result['valid']=False;result['error']=str(exc)
    return result
