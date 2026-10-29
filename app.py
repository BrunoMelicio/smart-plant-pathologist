import io
import time
import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from PIL import Image, ImageOps, UnidentifiedImageError
from pathologist_engine import PlantPathologistClient
from inspection import measure_image

ROOT = Path(__file__).resolve().parent
app = FastAPI(title='Folia · Plant inspection', version='2.0.0')
app.mount('/static', StaticFiles(directory=ROOT/'static'), name='static')
pathologist_client = PlantPathologistClient()
SAMPLE_PATHS = dict(healthy='sample_healthy_monstera.jpg', chlorosis='sample_iron_chlorosis.jpg', fungal='sample_fungal_leaf_spot.jpg', pest='sample_spider_mite_damage.jpg')
Image.MAX_IMAGE_PIXELS = 25_000_000

@app.get('/health')
def health():
    return dict(status='online', model=pathologist_client.model, ollama_base_url=pathologist_client.base_url)

@app.get('/')
def index_ui():
    return FileResponse(ROOT/'static/index.html')

@app.post('/diagnose')
async def diagnose(image: UploadFile = File(None), sample_key: Optional[str] = Form(None)):
    started = time.perf_counter()
    try:
        if image and image.filename:
            content = await image.read(15 * 1024 * 1024 + 1)
            if len(content) > 15 * 1024 * 1024:
                raise HTTPException(413, 'Choose a photo smaller than 15 MB.')
            pil = Image.open(io.BytesIO(content))
        elif sample_key in SAMPLE_PATHS:
            pil = Image.open(ROOT/'static/samples'/SAMPLE_PATHS[sample_key])
        else:
            raise HTTPException(400, 'Upload a plant photo or choose a reference sample.')
        pil = ImageOps.exif_transpose(pil).convert('RGB')
        if min(pil.size) < 32:
            raise HTTPException(422, 'Use a larger photo (at least 32 pixels on each side).')
        dimensions = list(pil.size)
        measurements = await run_in_threadpool(measure_image, pil)
        # Sample labels never override the model's observations in this workspace.
        result = await run_in_threadpool(pathologist_client.diagnose_plant, pil, None)
        data = result.model_dump()
        data.update(measurements)
        data.update(inspection_id=uuid.uuid4().hex[:8].upper(), duration_seconds=round(time.perf_counter()-started,2), dimensions=dimensions,
                    probability=None, probability_note='This model does not provide calibrated diagnostic probabilities.',
                    classification_method='Rule-based screening of model observations; possible causes, not confirmed diagnoses.', model=pathologist_client.model,
                    source='Reference photo' if sample_key else 'Uploaded photo')
        return data
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(422, 'This photo cannot be read. Use a JPEG, PNG or WebP image under 25 megapixels.')
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))
