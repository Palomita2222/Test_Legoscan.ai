from flask import Flask, render_template, request, send_file
import pandas as pd
import io
import requests
from requests_oauthlib import OAuth1

app = Flask(__name__)

# BrickLink credentials (replace with your real values)
CONSUMER_KEY = 'your_consumer_key'
CONSUMER_SECRET = 'your_consumer_secret'
TOKEN = 'your_token'
TOKEN_SECRET = 'your_token_secret'
auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, TOKEN, TOKEN_SECRET)

scanned_sets = {}
# scanned_sets = {
#     "75192": {"name": "Millennium Falcon", "avg_price": 799.00}
# }

def get_price_and_name(lego_id):
    name_url = f"https://api.bricklink.com/api/store/v1/items/SET/{lego_id}"
    price_url = f"https://api.bricklink.com/api/store/v1/price-guide/SET/{lego_id}?new_or_used=N&guide_type=sold"

    name_resp = requests.get(name_url, auth=auth)
    price_resp = requests.get(price_url, auth=auth)

    if name_resp.status_code == 200 and price_resp.status_code == 200:
        name = name_resp.json()['data'].get('name', 'Unknown')
        avg_price = price_resp.json()['data'].get('avg_price', None)
        return name, avg_price
    return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_code', methods=['POST'])
def submit_code():
    lego_id = request.json.get('lego_id')
    if not lego_id or not lego_id.isdigit():
        return {'error': 'Invalid ID'}, 400

    if lego_id in scanned_sets:
        return {'message': 'Already scanned'}, 200

    name, avg_price = get_price_and_name(lego_id)
    if name:
        scanned_sets[lego_id] = {'name': name, 'avg_price': avg_price}
        return {'id': lego_id, 'name': name, 'avg_price': avg_price}, 200
    else:
        return {'error': 'LEGO set not found'}, 404

@app.route('/export')
def export_excel():
    if not scanned_sets:
        return "No data to export", 400

    df = pd.DataFrame([
        {'id': id, 'name': data['name'], 'avg_price': data['avg_price']}
        for id, data in scanned_sets.items()
    ])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, download_name='lego_scanned.xlsx', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
