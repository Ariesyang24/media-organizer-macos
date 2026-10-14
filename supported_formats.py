"""Central media-format registry used by scanning and recognition."""

STANDARD_PHOTOS={
    '.jpg','.jpeg','.jpe','.jfif','.png','.webp','.bmp','.tif','.tiff',
    '.heic','.heif','.avif','.jxl',
}

RAW_PHOTOS={
    # Adobe / generic
    '.dng',
    # Canon
    '.crw','.cr2','.cr3',
    # Nikon
    '.nef','.nrw',
    # Sony
    '.arw','.srf','.sr2',
    # Fujifilm
    '.raf',
    # Panasonic / Leica
    '.rw2','.rwl',
    # Olympus / OM System
    '.orf','.ori',
    # Pentax
    '.pef','.ptx',
    # Sigma / Foveon
    '.x3f',
    # Hasselblad
    '.3fr','.fff',
    # Phase One / Leaf / Mamiya
    '.iiq','.mos','.mef',
    # Kodak / Epson / Minolta / Samsung
    '.dcr','.kdc','.erf','.mrw','.srw',
}

STANDARD_VIDEOS={
    '.mp4','.mov','.m4v','.avi','.mkv','.webm','.wmv','.asf',
    '.mpg','.mpeg','.mpe','.ts','.m2t','.mts','.m2ts',
    '.mxf','.vob','.mod','.tod','.3gp','.3g2','.flv','.f4v','.ogv',
}

PRO_VIDEO_FORMATS={
    '.crm',   # Canon Cinema RAW Light
    '.nev',   # Nikon N-RAW
    '.braw',  # Blackmagic RAW
    '.r3d',   # REDCODE RAW
}

PHOTOS=STANDARD_PHOTOS|RAW_PHOTOS
VIDEOS=STANDARD_VIDEOS|PRO_VIDEO_FORMATS
MEDIA_EXTENSIONS=PHOTOS|VIDEOS
PREVIEW_FALLBACK_PHOTOS=RAW_PHOTOS|{'.heic','.heif','.avif','.jxl'}
