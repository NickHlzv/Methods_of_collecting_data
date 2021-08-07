import requests
import json

API_KEY = 'fdb2abab53832eb8205a102170c5f034'
USER_AGENT = 'wunderkind777'
headers = {
    'user-agent': USER_AGENT
}

payload = {
    'api_key': API_KEY,
    'method': 'chart.gettopartists',
    'format': 'json'
}

r = requests.get('https://ws.audioscrobbler.com/2.0/', headers=headers, params=payload)
print(r.status_code)


def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)


jprint(r.json())

with open('data_ex2.json', 'w') as f:
    json.dump(r.json(), f)
