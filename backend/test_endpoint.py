import requests
import sys

url = "http://localhost:8000/api/twilio/outbound-answer?business_id=demo-clinic-1"
response = requests.post(url)
print(response.text)
