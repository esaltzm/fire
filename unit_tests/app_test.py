import os
import sys
import time
import requests
import pytest

app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, app_dir)

from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@pytest.mark.usefixtures("client")
class TestFireReport:

    def test_sms_reply(self, client):
        time.sleep(120)
        response = client.post('/sms', data={'Body': 'PCT'})
        assert response.status_code == 200
        assert 'Total fires within 50 miles of the PCT' in str(response.data)

        response = client.post('/sms', data={'Body': 'AT'})
        assert response.status_code == 200
        assert 'Sorry, we could not find a supported trail name in your message.' in str(response.data)
