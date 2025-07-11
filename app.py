from flask import Flask, render_template, request, jsonify
import os
import cv2
import pytesseract
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  # adjust if needed

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Process image with OpenCV
    img = cv2.imread(filepath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # OCR
    text = pytesseract.image_to_string(thresh, config='--psm 6')
    
    # Basic filtering to extract LEGO-like codes (digits, maybe with dashes)
    import re
    codes = re.findall(r'\b\d{5,7}\b', text)

    return jsonify({"codes": codes})

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
