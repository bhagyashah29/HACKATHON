import requests
from flask import current_app


def parse_receipt_image(file_path: str) -> dict:
    api_key = current_app.config.get('OCR_SPACE_API_KEY')
    if not api_key:
        # OCR optional; return empty extraction
        return {}
    url = 'https://api.ocr.space/parse/image'
    with open(file_path, 'rb') as f:
        resp = requests.post(url, data={'apikey': api_key, 'language': 'eng'}, files={'file': f}, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Very naive extraction
        parsed_results = data.get('ParsedResults') or []
        text = '\n'.join([p.get('ParsedText', '') for p in parsed_results])
        return {'raw_text': text}
