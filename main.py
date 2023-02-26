import os
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

@app.route('/sms', methods=['POST'])

def sms_reply():
    resp = MessagingResponse()
    resp.message('reply')
    return str(resp)

if __name__ == '__main__':
    app.run(host = LISTEN_ADDRESS, port = LISTEN_PORT)