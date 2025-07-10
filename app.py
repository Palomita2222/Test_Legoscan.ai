from flask import Flask, render_template, Response, jsonify
import cv2
import pytesseract
import re
import requests
from requests_oauthlib import OAuth1

app = Flask(__name__)

# BrickLink API credentials
CONSUMER_KEY = 'your_consumer_key'
CONSUMER_SECRET = 'your_consumer_secret'
TOKEN = 'your_token_value'
TOKEN_SECRET = 'your_token_secret'
auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, TOKEN, TOKEN_SECRET)

camera = cv2.VideoCapture(0)  # 0 = default webcam

def get_price_guide(item_id):
    url = f"https://api.bricklink.com/api/store/v1/price-guide/SET/{item_id}?new_or_used=N&guide_type=sold"
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        return response.json().get("data", {})
    return "error"

def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        # OCR
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
        lego_ids = re.findall(r'\b\d{3,7}\b', text)  # LEGO IDs are usually 3-7 digits

        # Overlay found ID
        if lego_ids:
            cv2.putText(frame, f"LEGO ID: {lego_ids[0]}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            print(lego_ids)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/scan')
def scan_and_fetch():
    # Read one frame to scan
    success, frame = camera.read()
    if not success:
        return jsonify({'error': 'Camera read failed'})

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    print(text)
    lego_ids = re.findall(r'\b\d{3,7}\b', text)

    if not lego_ids:
        return jsonify({'error': 'No LEGO ID found'})

    lego_id = lego_ids[0]
    price_data = get_price_guide(lego_id)

    if price_data:
        return jsonify({
            'lego_id': lego_id,
            'min_price': price_data.get('min_price'),
            'avg_price': price_data.get('avg_price'),
            'max_price': price_data.get('max_price'),
            'qty_sold': price_data.get('qty_sold')
        })
    else:
        return jsonify({'error': 'BrickLink data not found'})

if __name__ == '__main__':
    app.run(debug=True)
