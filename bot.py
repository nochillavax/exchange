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

def notify_dev(message):
    if message != '':
        text = '%s' % (message)
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        bot.sendMessage(chat_id=DEV_NOTIFICATION_ID, text=text)

def notify_tg_group(message):
    if message != '':
        text = '%s' % (message)
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        bot.sendMessage(chat_id=CHAT_NOTIFICATION_ID, text=text)

def read_users_json():
    with open('users.json', 'r') as openfile:
        # Reading from json file
        json_object = json.load(openfile)

    return json_object

def get_username(conn, address):
    address = address.lower()
    username = sql.get_username_from_db(conn, address)
    if username != None:
        return username
    else:
        username = arena.get_username(address)
        if username != None:
            sql.add_username_to_db(conn, address, username)
        else:
            try:
                users = read_users_json()
                if address.lower() in users:
                    username = users[address.lower()]
                else:
                    username = None
            except:
                pass

            if username == None:
                username = address.lower()
                sql.add_username_to_db(conn, address, username)
        return username


def perform_transfers():
    conn = sql.create_connection(PATH_TO_DB)
    sql.create_tables(conn)
    payables = sql.get_waiting_transfers(conn)
    print('transfers waiting to be sent:')
    print(json.dumps(payables, indent=4))
    if len(payables) != 0:
        avapi = AvalancheAPI()
        for xfer in payables:
            sql.update_transfer_to_pending(conn, xfer['hash'])

        for xfer in payables:
            print('attempting:')
            print(xfer)
            time.sleep(3)
            try:
                transferTxn = avapi.transfer(TOKEN_ADDRESS, xfer['to'], xfer['amount'])
                if transferTxn != 'None':
                    notify_dev('transferred %s NOCHILL to %s - hash: %s' % (xfer['amount_readable'], xfer['username'], scan.make_explorer_link(transferTxn)))
                    sql.update_transaction_with_transfer_data(conn, xfer['hash'], transferTxn, xfer['amount_readable'])
                    arena.notify_arena(BEARER_TOKEN, xfer['username'], xfer['incoming'], xfer['amount_readable'], xfer['hash'], transferTxn)
                else:
                    notify_dev('transfer failed. retrying later. %s, %s NOCHILL, wallet %s' % (xfer['username'], xfer['amount_readable'], xfer['to']))
                    sql.update_transfer_to_waiting(conn, xfer['hash'])
                time.sleep(30)
            except Exception as e:
                print(e)
                sql.update_transfer_to_waiting(conn, xfer['hash'])
                #notify_dev('transfer failed again. not retrying. please manually tip %s NOCHILL amount %s and update db. wallet: %s' % (xfer['username'], xfer['amount_readable'], xfer['to']))


def perform_buys():
    payables = scan.get_transfers(SNOWSCAN_API_KEY, MY_WALLET)
    #manual_missed_txn = {'hash': '0xe0bf3bd65cdf43975b63df4ad7ec0a0317548418c96265d359a63323dc1a0d7a',
    # 'from': '0x0136E98f756d267e2c923049B362c193daaa5ad9',
    # 'value': str(int(2.369* 10**18))}

    #payables.append(manual_missed_txn)
    #print(payables)
    if len(payables) != 0:
        conn = sql.create_connection(PATH_TO_DB)
        avapi = AvalancheAPI()
        sql.create_tables(conn)

        print('payables count: ',len(payables))
        total_buy_amount = 0
        payables_considered = []
        for payable in payables:
            if not sql.check_transaction(conn, payable['hash']):
                total_buy_amount += int(payable['value'])
                username = get_username(conn, payable['from'])
                notify_dev('got a transaction from %s - %s avax - hash: %s' % (username, int(payable['value'])/10**BASE_DECIMALS, scan.make_explorer_link(payable['hash'])))
                sql.add_transaction(conn, payable['hash'], int(payable['value'])/10**BASE_DECIMALS, username)
                payables_considered.append(payable)

        if len(payables_considered) != 0:
            # reduce service fee
            total_buy_amount_less_fee = int(total_buy_amount * (1-SERVICE_FEE))

            amt = None
            buy_success = False
            buy_txn_id = None
            try:
                amt, buy_success, buy_txn_id = avapi.buy(TOKEN_ADDRESS, total_buy_amount_less_fee)
                print(amt)
                print(buy_success)
                print(buy_txn_id)
                buy_success = True
                msg = 'Batch Buy succeeded for %s incoming transactions.' % (len(payables_considered))
                print(msg)
                notify_dev(msg)
            except Exception as e:
                print(e)
                for payable in payables_considered:
                    sql.remove_transaction(conn, payable['hash'])
                buy_success = False
                msg = 'Batch Buy failed for %s incoming transactions. They have been removed from the db and will be retried shortly.' % (len(payables_considered))
                print(msg)
                notify_dev(msg)

            if buy_success == True: # Check if the transaction went through
                qty_purchased = int(amt)/10**TOKEN_DECIMALS
                for payable in payables_considered:
                    pct_to_send = float(payable['value']) / float(total_buy_amount)
                    owed = float(qty_purchased) * pct_to_send
                    sql.update_transaction_with_buy_data(conn, payable['hash'], int(payable['value'])/10**BASE_DECIMALS, buy_txn_id, owed)
                    username = get_username(conn, payable['from'])
                    notify_tg_group('%s tipped %s to nochillexchange' % (username, int(payable['value'])/10**BASE_DECIMALS))

if __name__ == "__main__":
    perform_buys()
    perform_transfers()
