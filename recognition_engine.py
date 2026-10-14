import json, subprocess
from pathlib import Path
import cv2, imagehash, numpy as np
from PIL import ExifTags, Image

ROOT=Path(__file__).resolve().parent
EXIFTOOL=ROOT/'tools'/'exiftool.exe'
from portable_paths import find_ffprobe
FFPROBE=find_ffprobe()
from supported_formats import PREVIEW_FALLBACK_PHOTOS, RAW_PHOTOS, VIDEOS
RAW_EXTENSIONS=RAW_PHOTOS

def command_json(args,timeout=20):
    try:
        p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout,creationflags=0x08000000)
        return json.loads(p.stdout) if p.returncode==0 and p.stdout.strip() else None
    except Exception:return None

def rich_metadata(path):
    data={}
    video_extensions=VIDEOS
    if path.suffix.lower() not in video_extensions:
        try:
            with Image.open(path) as im:
                exif={ExifTags.TAGS.get(key,key):value for key,value in im.getexif().items()}
                make=str(exif.get('Make','')).strip();model=str(exif.get('Model','')).strip()
                def number(value):
                    try:return float(value) if value is not None else None
                    except (TypeError,ValueError,ZeroDivisionError):return value
                latitude=longitude=None
                try:
                    gps_ifd=im.getexif().get_ifd(ExifTags.IFD.GPSInfo)
                    gps={ExifTags.GPSTAGS.get(key,key):value for key,value in gps_ifd.items()}
                    def decimal(value):
                        return float(value[0])+float(value[1])/60+float(value[2])/3600
                    if gps.get('GPSLatitude'):
                        latitude=decimal(gps['GPSLatitude'])*(-1 if gps.get('GPSLatitudeRef')=='S' else 1)
                    if gps.get('GPSLongitude'):
                        longitude=decimal(gps['GPSLongitude'])*(-1 if gps.get('GPSLongitudeRef')=='W' else 1)
                except Exception:pass
                data={'camera':' '.join(dict.fromkeys(x for x in (make,model) if x)),
                      'lens':str(exif.get('LensModel','')),'iso':exif.get('ISOSpeedRatings') or exif.get('PhotographicSensitivity'),
                      'aperture':number(exif.get('FNumber')),'shutter':number(exif.get('ExposureTime')),
                      'focal':number(exif.get('FocalLength')),'gps':(latitude,longitude),'duration':None,
                      'width':im.width,'height':im.height,'fps':None,
                      'captured':exif.get('DateTimeOriginal') or exif.get('DateTimeDigitized')}
                return data
        except Exception:
            pass
    result=command_json([str(EXIFTOOL),'-j','-n','-DateTimeOriginal','-CreateDate','-MediaCreateDate','-Make','-Model','-LensModel','-ISO','-FNumber','-ExposureTime','-FocalLength','-GPSLatitude','-GPSLongitude','-Duration','-ImageWidth','-ImageHeight','-VideoFrameRate',str(path)]) if EXIFTOOL.exists() else None
    if result:
        x=result[0]; data={'camera':' '.join(dict.fromkeys(str(x.get(k,'')).strip() for k in ('Make','Model') if x.get(k))).strip(),'lens':str(x.get('LensModel','')),'iso':x.get('ISO'),'aperture':x.get('FNumber'),'shutter':x.get('ExposureTime'),'focal':x.get('FocalLength'),'gps':(x.get('GPSLatitude'),x.get('GPSLongitude')),'duration':x.get('Duration'),'width':x.get('ImageWidth'),'height':x.get('ImageHeight'),'fps':x.get('VideoFrameRate')}
        data['captured']=x.get('DateTimeOriginal') or x.get('MediaCreateDate') or x.get('CreateDate')
    if path.suffix.lower() in VIDEOS and not data.get('duration') and FFPROBE is not None:
        x=command_json([str(FFPROBE),'-v','error','-show_entries','format=duration:stream=codec_type,width,height,r_frame_rate','-of','json',str(path)]) or {}
        data['duration']=(x.get('format') or {}).get('duration'); video=next((s for s in x.get('streams',[]) if s.get('codec_type')=='video'),{}); data['width']=video.get('width');data['height']=video.get('height');data['fps']=video.get('r_frame_rate')
    return data

def decode(path):
    try:
        image=cv2.imdecode(np.fromfile(str(path),dtype=np.uint8),cv2.IMREAD_COLOR)
        if image is not None:return image
    except Exception:pass
    if path.suffix.lower() in PREVIEW_FALLBACK_PHOTOS and EXIFTOOL.exists():
        for tag in ('-PreviewImage','-JpgFromRaw','-ThumbnailImage'):
            try:
                process=subprocess.run([str(EXIFTOOL),'-b',tag,str(path)],capture_output=True,timeout=30,creationflags=0x08000000)
                if process.returncode==0 and process.stdout:
                    image=cv2.imdecode(np.frombuffer(process.stdout,dtype=np.uint8),cv2.IMREAD_COLOR)
                    if image is not None:return image
            except Exception:pass
    return None

def white_background_photo(image,gray):
    """Separate intentional white studio backgrounds from clipped highlights."""
    height,width=gray.shape; edge=max(2,min(height,width)//20)
    border=np.concatenate((gray[:edge,:].ravel(),gray[-edge:,:].ravel(),gray[edge:-edge,:edge].ravel(),gray[edge:-edge,-edge:].ravel()))
    hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
    border_white=float((border>245).mean())
    foreground=float(((gray<238)|(hsv[:,:,1]>28)).mean())
    subject_detail=float(((hsv[:,:,1]>35)&(gray<245)).mean())+float((gray<150).mean())
    return border_white>.82 and .025<foreground<.82 and subject_detail>.035

def analyze(path,kind,exact_hash):
    result={'valid':True,'blur':None,'exposure':'正常','quality':0.0,'phash':None,'meta':rich_metadata(path)}
    if kind!='照片':return result
    image=decode(path)
    if image is None:
        if path.suffix.lower() in PREVIEW_FALLBACK_PHOTOS and result['meta'].get('width') and result['meta'].get('height'):
            result.update(valid=True,exposure='RAW待预览',quality=50,exact=exact_hash,raw_preview=False);return result
        result.update(valid=False,exposure='文件异常待检查',quality=-1,exact=exact_hash);return result
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY); blur=float(cv2.Laplacian(gray,cv2.CV_64F).var()); mean=float(gray.mean()); dark=float((gray<20).mean()); bright=float((gray>245).mean()); white_bg=white_background_photo(image,gray)
    raw_exposure=('严重欠曝' if dark>.45 or mean<45 else '严重过曝' if bright>.35 or mean>220 else '轻微欠曝' if mean<75 else '轻微过曝' if mean>190 else '正常')
    exposure='正常' if white_bg else raw_exposure
    sharp=min(100,blur/5); penalty=35 if '严重' in exposure else 15 if '轻微' in exposure else 0; quality=max(0,sharp-penalty)
    try:
        rgb=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        ph=str(imagehash.phash(Image.fromarray(rgb)))
    except Exception:ph=None
    subject_present=float((gray<238).mean())>.025
    result.update(blur=blur,exposure=exposure,raw_exposure=raw_exposure,quality=quality,phash=ph,
                  exact=exact_hash,white_background=white_bg,subject_present=subject_present)
    return result

def group(rows):
    exact={}; photos=[]
    for i,r in enumerate(rows):
        a=r.get('analysis',{}); exact.setdefault(a.get('exact'),[]).append(i)
        if a.get('phash'):photos.append(i)
    for values in exact.values():
        if len(values)>1:
            label='完全重复 '+str(min(values)+1)
            for i in values:rows[i]['duplicate']=label
    parent=list(range(len(rows)))
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    for pos,i in enumerate(photos):
        hi=imagehash.hex_to_hash(rows[i]['analysis']['phash'])
        for j in photos[pos+1:]:
            if rows[i].get('duplicate') or rows[j].get('duplicate'):continue
            if hi-imagehash.hex_to_hash(rows[j]['analysis']['phash'])<=6:parent[find(j)]=find(i)
    near={}
    for i in photos:near.setdefault(find(i),[]).append(i)
    for values in near.values():
        if len(values)>1:
            label='近似重复 '+str(min(values)+1)
            for i in values:rows[i]['duplicate']=label
    bursts={}
    for i,r in enumerate(rows):
        if r['kind']=='照片':bursts.setdefault((r['p'].parent,r['dev'],int(r['ts']//3)),[]).append(i)
    for values in bursts.values():
        if len(values)>=2:
            best=max(values,key=lambda i:rows[i]['analysis']['quality']);label='连拍 '+str(min(values)+1)
            for i in values:rows[i]['burst']=label;rows[i]['recommend']='推荐保留' if i==best else '备选'
    for r in rows:
        if not r.get('recommend'):r['recommend']='建议检查' if r['analysis'].get('quality',100)<25 or r['analysis'].get('exposure')!='正常' else '正常'
