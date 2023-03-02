import os
import re
import time
import requests
import threading
from firetracker import FireTracker
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
if os.environ.get('FLASK_DEBUG'):
    DEBUG = True
    DEVELOPMENT = True
    LISTEN_ADDRESS = '127.0.0.1'
    LISTEN_PORT = 8080
else:
    DEBUG = False
    TESTING = False
    LISTEN_ADDRESS = '209.94.59.175'
    LISTEN_PORT = 5000

err_text = 'Sorry, an error occurred while generating the fire report.\nPlease try again later.'

fire_reports = {
    'PCT': err_text,
    'CT': err_text,
    'PNT': err_text,
    'AZT': err_text,
    'CDT': err_text
}

trail_names = {
    'PCT': 'PCT',
    'Pacific Crest Trail': 'PCT',
    'CT': 'CT',
    'Colorado Trail': 'CT',
    'PNT': 'PNT',
    'Pacific Northwest Trail': 'PNT',
    'AZT': 'AZT',
    'Arizona Trail': 'AZT',
    'CDT': 'CDT',
    'Continental Divide Trail': 'CDT'
}

def retrieve_reports():
    api_url = 'https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Current_WildlandFire_Perimeters/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json'
    while True:
        response = requests.get(api_url)
        data = response.json()
        current_fires = data['features']
        for trail in fire_reports.keys():
            tracker = FireTracker(trail, current_fires)
            success = tracker.create_SMS()
            if success:
                fire_reports[trail] = tracker.text
            else:
                fire_reports[trail] = err_text
        time.sleep(4 * 3600) # Retrieve new reports every 4 hours

trail_pattern = re.compile('|'.join(trail_names.keys()), re.IGNORECASE)

@app.route('/test', methods=['GET'])
def test():
    return 'testing'

@app.route('/sms', methods=['POST'])
def sms_reply():
    resp = MessagingResponse()
    message = request.form.get('Body', '').strip()
    match = trail_pattern.search(message)
    if match:
        trail = match.group(0).upper()
        resp.message(fire_reports[trail_names[trail]])
    else:
        resp.message('Sorry, we could not find a supported trail name in your message.\nPlease enter one of the following: PCT, CT, AZT, PNT, or CDT\nMore trails are forthcoming!')
    return str(resp)

ongoing_thread = threading.Thread(target=retrieve_reports)
ongoing_thread.start()
app.run(host=LISTEN_ADDRESS, port=LISTEN_PORT, threaded=True, debug=False)
