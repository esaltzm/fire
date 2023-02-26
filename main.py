import os
import re
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from firetracker import FireTracker

app = Flask(__name__)
if os.environ.get('mode') == 'dev':
    DEBUG = True
    DEVELOPMENT = True
    LISTEN_ADDRESS = '127.0.0.1'
    LISTEN_PORT = 5000
else:
    DEBUG = False
    TESTING = False
    LISTEN_ADDRESS = '209.94.59.175'
    LISTEN_PORT = 5000

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

trail_pattern = re.compile('|'.join(trail_names.keys()), re.IGNORECASE)

@app.route('/sms', methods=['POST'])
def sms_reply():
    resp = MessagingResponse()
    message = request.values.get('Body', '').strip()
    match = trail_pattern.search(message)
    if match:
        trail = match.group(0).upper()
        tracker = FireTracker(trail)
        success = tracker.create_SMS()
        resp.message(tracker.text) if success else resp.message('Sorry, an error occurred while generating the fire report.\nPlease try again later.')
    else:
        resp.message('Sorry, we could not find a supported trail name in your message.\nPlease enter one of the following: PCT, CT, AZT, PNT, or CDT\nMore trails are forthcoming!')
    return str(resp)

if __name__ == '__main__':
    app.run(host = LISTEN_ADDRESS, port = LISTEN_PORT)