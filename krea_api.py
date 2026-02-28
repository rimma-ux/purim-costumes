import os
import requests

BASE_URL = 'https://api.krea.ai'


def _headers(json=False):
    token = os.environ.get('KREA_API_TOKEN', '')
    h = {'Authorization': f'Bearer {token}'}
    if json:
        h['Content-Type'] = 'application/json'
    return h


def upload_asset(file_data, filename, content_type='image/jpeg'):
    """Upload a file to Krea and return the asset image_url."""
    files = {'file': (filename, file_data, content_type)}
    resp = requests.post(f'{BASE_URL}/assets', headers=_headers(), files=files, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # Docs say response has an image_url field
    url = (
        data.get('image_url')
        or data.get('url')
        or (data.get('data') or {}).get('image_url')
        or (data.get('data') or {}).get('url')
    )
    if not url:
        raise ValueError(f"Could not find URL in upload response: {data}")
    return url


def generate_image(prompt, image_url):
    """Trigger image generation. Returns job_id."""
    payload = {
        'prompt': prompt,
        'imageUrls': [image_url],   # array, not single string
        'aspectRatio': '2:3',       # camelCase per docs
    }
    resp = requests.post(
        f'{BASE_URL}/generate/image/google/nano-banana-pro',
        headers=_headers(json=True),
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    job_id = (
        data.get('job_id')
        or data.get('id')
        or (data.get('data') or {}).get('job_id')
        or (data.get('data') or {}).get('id')
    )
    if not job_id:
        raise ValueError(f"Could not find job ID in response: {data}")
    return job_id


def poll_generation(job_id):
    """Poll job status. Returns dict with status and optional image url."""
    resp = requests.get(
        f'{BASE_URL}/jobs/{job_id}',   # /jobs/{id} per docs
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    status = data.get('status') or (data.get('data') or {}).get('status')

    # Extract result URL
    result = data.get('result') or (data.get('data') or {}).get('result') or {}
    image_url = None
    if isinstance(result, dict):
        urls = result.get('urls', [])
        image_url = urls[0] if urls else result.get('url')
    elif isinstance(result, list) and result:
        image_url = result[0]

    # Fallback: top-level url
    if not image_url:
        image_url = data.get('url') or (data.get('data') or {}).get('url')

    return {
        'status': status,
        'url': image_url,
    }
