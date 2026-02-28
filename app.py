import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import krea_api
from costume_parser import parse_costumes

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Parse costumes once at startup
CATEGORIES = parse_costumes()

# Build a flat lookup: costume_id → costume dict (for prompt retrieval)
COSTUME_MAP = {
    costume['id']: costume
    for category in CATEGORIES
    for costume in category['costumes']
}


@app.route('/')
def index():
    return render_template('index.html', categories=CATEGORIES)


@app.route('/preview-image')
def preview_image():
    return send_from_directory(app.root_path, 'Preview window picture.png')


@app.route('/api/upload-photo', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo provided'}), 400
    photo = request.files['photo']
    if not photo.filename:
        return jsonify({'error': 'No file selected'}), 400
    try:
        url = krea_api.upload_asset(
            photo.read(),
            photo.filename,
            photo.content_type or 'image/jpeg',
        )
        return jsonify({'url': url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    prompt = data.get('prompt')
    image_url = data.get('image_url')

    if not prompt:
        return jsonify({'error': 'Missing prompt'}), 400
    if not image_url:
        return jsonify({'error': 'Missing image_url'}), 400

    try:
        generation_id = krea_api.generate_image(prompt, image_url)
        return jsonify({'generation_id': generation_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generation/<generation_id>')
def get_generation(generation_id):
    try:
        result = krea_api.poll_generation(generation_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download-image')
def download_image():
    """Proxy an image URL for download (avoids CORS issues)."""
    import requests as req
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        r = req.get(url, timeout=30)
        r.raise_for_status()
        from flask import Response
        return Response(
            r.content,
            content_type=r.headers.get('Content-Type', 'image/jpeg'),
            headers={'Content-Disposition': 'attachment; filename="purim-costume.jpg"'},
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5051, debug=True)
