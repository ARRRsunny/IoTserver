import requests

url = 'http://192.168.194.251:8080/submit-data'
data = {
    "Present": true,
    "duration": 130,
    "wet area": false,
    "moisture": 66,
    "last record time duration": 14
}

response = requests.post(url, json=data)

print(response.json())