import os
import time
from botutils import scan, arena, sql
from dotenv import load_dotenv
#import threading
import json

load_dotenv()

PATH_TO_DB = os.environ['PATH_TO_DB']
SERVICE_FEE = float(os.environ['SERVICE_FEE'])
TOKEN_ADDRESS = os.environ['TOKEN_ADDRESS']
MY_WALLET = os.environ['MY_WALLET']
SNOWSCAN_API_KEY = os.environ['SNOWSCAN_API_KEY']
BEARER_TOKEN = 'Bearer ' + os.environ['BEARER_TOKEN']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
DEV_NOTIFICATION_ID = os.environ['DEV_NOTIFICATION_ID']
CHAT_NOTIFICATION_ID = os.environ['CHAT_NOTIFICATION_ID']
BUYS_ENABLED = True
TOKEN_DECIMALS = int(os.environ['TOKEN_DECIMALS'])
BASE_DECIMALS = 18

def read_users_json():
    with open('users.json', 'r') as openfile:
        # Reading from json file
        json_object = json.load(openfile)

    return json_object

new_users = read_users_json()
conn = sql.create_connection(PATH_TO_DB)

for user in new_users:
    if sql.get_wallet(conn, new_users[user]) == None:
        print('User not found. Adding. %s %s' % (new_users[user], user))
        sql.add_username_to_db(conn, user.lower(), new_users[user])
