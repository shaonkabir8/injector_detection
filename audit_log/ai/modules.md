# Python Modules Analysis

## Module Dependencies

### detection.py
```
from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
```

### __init__.py
```
from .detection import (
```

### queue.py
```
from __future__ import annotations
import logging
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from modules.cache import cache
from modules.job_queue import enqueue, get_job, list_jobs, queue_depth
from utils.image import decode_upload, resize_for_inference
from config import settings
```

### detect.py
```
from __future__ import annotations
import logging
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from config import settings
from modules.cache              import cache
from modules.quality_checker    import check_image_quality
from modules.vehicle_detector   import detect_vehicles, run_raw_yolo
from modules.cargo_segmenter    import segment_cargo
from modules.load_detector      import detect_load
```

### health.py
```
from fastapi import APIRouter
from pydantic import BaseModel
```

### video.py
```
from __future__ import annotations
import asyncio
import logging
import requests as req_lib
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from modules.video_processor import process_video, process_stream
from modules.source_resolver import detect_source_type
from modules.url_safety import is_url_safe
from modules.youtube_resolver import resolve_youtube_live
```

### __init__.py
```
