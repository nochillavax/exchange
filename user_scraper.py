import logging
import requests
from datetime import datetime
import json
#from dotenv import load_dotenv
import os


#load_dotenv()

BEARER = '' # bearer token WITHOUT the 'Bearer ' part

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Origin': 'https://starsarena.com',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Authorization': f'Bearer {BEARER}',
    'Connection': 'keep-alive',
}


def get_latest_trades():
    try:
        headers = HEADERS.copy()  # Copy the headers and add Authorization dynamically
        headers['Authorization'] = f'Bearer {BEARER}'
        response = requests.get('https://api.starsarena.com/trade/recent', headers=headers, timeout=2)
        response.raise_for_status()
        trades = response.json().get('trades', [])
        # logging.info(trades)
        # logging.info(json.dumps({'message': 'Successfully retrieved trades.'}))
        return trades
    except requests.exceptions.RequestException as e:
        logging.info(f"Failed to retrieve trades: {e}")
        return []  # Return an empty list in case of an error
    except json.JSONDecodeError as e:
        # logging.info(f"Error decoding JSON: {e}")
        return []  # Return an empty list in case of a JSON decoding error


def get_latest_joiners():
    try:
        headers = HEADERS.copy()  # Copy the headers and add Authorization dynamically
        headers['Authorization'] = f'Bearer {BEARER}'
        response = requests.get('https://api.starsarena.com/user/page', headers=headers, timeout=2)
        response.raise_for_status()
        # logging.info(response.json())
        trades = response.json().get('users', [])
        return trades
    except requests.exceptions.RequestException as e:
        logging.info(f"Failed to retrieve trades: {e}")
        return []  # Return an empty list in case of an error
    except json.JSONDecodeError as e:
        # logging.info(f"Error decoding JSON: {e}")
        return []  # Return an empty list in case of a JSON decoding error

def read_json():
    with open('users.json', 'r') as openfile:
        # Reading from json file
        json_object = json.load(openfile)

    return json_object

def write_json(json_object):
    with open("users.json", "w") as outfile:
        outfile.write(json.dumps(json_object))

#print(get_latest_trades())
userJson = read_json()
if userJson != {}:
    for user in get_latest_joiners():
        userJson[user['address']] = user['twitterHandle']

    write_json(userJson)
