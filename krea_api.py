import os
import base64
import uuid
import requests
from PIL import Image
import io

BASE_URL = 'https://generativelanguage.googleapis.com/v1beta'
MODEL = 'gemini-3-pro-image-preview'

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')


def _api_key():
    return os.environ.get('GEMINI_API_KEY', '')


def _ensure_uploads():
    os.makedirs(UPLOADS_DIR, exist_ok=True)


def _to_jpeg_b64(file_data):
    """Convert any image bytes to base64-encoded JPEG."""
    with Image.open(io.BytesIO(file_data)) as img:
        out = io.BytesIO()
        img.convert('RGB').save(out, format='JPEG', quality=90)
        return base64.b64encode(out.getvalue()).decode('utf-8')


def upload_asset(file_data, filename, content_type='image/jpeg'):
    """Save uploaded photo locally. Returns a photo_id (used in place of a CDN URL)."""
    _ensure_uploads()
    photo_id = str(uuid.uuid4())
    path = os.path.join(UPLOADS_DIR, f'photo_{photo_id}.bin')
    with open(path, 'wb') as f:
        f.write(file_data)
    return photo_id


def generate_image(prompt, photo_id):
    """Call Gemini to generate a costumed portrait. Returns a result_id.
    Blocks until the image is returned (10–30 s typical).
    """
    _ensure_uploads()

    photo_path = os.path.join(UPLOADS_DIR, f'photo_{photo_id}.bin')
    with open(photo_path, 'rb') as f:
        image_b64 = _to_jpeg_b64(f.read())

    full_prompt = (
        f'Generate a realistic portrait photo of this exact person wearing this costume: {prompt}. '
        f'Preserve the person\'s face and features. '
        f'Portrait orientation, 2:3 aspect ratio.'
    )

    payload = {
        'contents': [{
            'parts': [
                {'inline_data': {'mime_type': 'image/jpeg', 'data': image_b64}},
                {'text': full_prompt},
            ]
        }],
        'generationConfig': {'responseModalities': ['IMAGE', 'TEXT']},
    }

    url = f'{BASE_URL}/models/{MODEL}:generateContent?key={_api_key()}'
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    for candidate in data.get('candidates', []):
        for part in candidate.get('content', {}).get('parts', []):
            inline = part.get('inlineData') or part.get('inline_data')
            if inline and inline.get('mimeType', inline.get('mime_type', '')).startswith('image/'):
                result_id = str(uuid.uuid4())
                img_bytes = base64.b64decode(inline['data'])
                # Normalise to JPEG regardless of what Gemini returned
                with Image.open(io.BytesIO(img_bytes)) as img:
                    out = io.BytesIO()
                    img.convert('RGB').save(out, format='JPEG', quality=95)
                result_path = os.path.join(UPLOADS_DIR, f'result_{result_id}.jpg')
                with open(result_path, 'wb') as f:
                    f.write(out.getvalue())
                return result_id

    raise ValueError(f'No image in Gemini response: {data}')


def poll_generation(result_id):
    """Return status dict. Since Gemini is synchronous the result is always ready."""
    path = os.path.join(UPLOADS_DIR, f'result_{result_id}.jpg')
    if os.path.exists(path):
        return {'status': 'completed', 'url': f'/api/result/{result_id}'}
    return {'status': 'processing', 'url': None}


def get_result_path(result_id):
    """Return the filesystem path to the result image, or None."""
    path = os.path.join(UPLOADS_DIR, f'result_{result_id}.jpg')
    return path if os.path.exists(path) else None
