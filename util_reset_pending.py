import os
from AvalancheAPI import AvalancheAPI
import telegram
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

def reset_pending():
    conn = sql.create_connection(PATH_TO_DB)
    sql.create_tables(conn)
    payables = sql.get_pending_transfers(conn)
    print('transfers waiting to be sent:')
    print(json.dumps(payables, indent=4))
    if len(payables) != 0:
        for xfer in payables:
            sql.update_transfer_to_waiting(conn, xfer['hash'])

reset_pending()
