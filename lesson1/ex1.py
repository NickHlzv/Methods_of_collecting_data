import requests
import json
url = 'https://api.github.com'
user='NickHlzv'
r = requests.get(f'{url}/users/{user}/repos')
with open('data.json', 'w') as f:
    json.dump(r.json(), f)
for i in r.json():
    print(i['name'])
