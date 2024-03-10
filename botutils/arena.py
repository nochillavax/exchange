import requests
import json
from botutils import scan

def notify_arena(bearer_token, username, tipped, amount, hashIn, hashOut):
    message = 'Thanks @%s for %s AVAX, your %s NOCHILL has been sent.<br/>%s' % (username, tipped, amount, scan.make_explorer_link(hashOut))
    message = message.replace('Thanks @None for ', 'Thanks Undetected Username for ')
    headers = {}
    headers['Content-Type'] = 'application/json'
    headers['Authorization'] = bearer_token

    payload = {}
    payload['content'] = message
    payload['files'] = []
    if float(tipped) >= 5.0:
        imageUrl = 'https://nochill.lol/assets/buybot.jpg'
        file = {"url":imageUrl,"isLoading":False, "fileType": "image"}
        payload['files'].append(file)
    payload['privacyType'] = 0
    r = requests.post('https://api.starsarena.com/threads', headers=headers, data=json.dumps(payload))

def notify_arena_leaderboard(bearer_token, message):
    headers = {}
    headers['Content-Type'] = 'application/json'
    headers['Authorization'] = bearer_token

    payload = {}
    payload['content'] = message
    payload['files'] = []
    payload['privacyType'] = 0
    r = requests.post('https://api.starsarena.com/threads', headers=headers, data=json.dumps(payload))

def get_username(address):
    username = None
    url = 'https://api.arenabook.xyz/user_info?user_address=eq.%s' % address
    r = requests.get(url)
    if r.status_code == 200:
        if len(r.json()) == 1:
            username = r.json()[0]['twitter_handle']

    return username
