import requests
import json
import sqlite3
from sqlite3 import Error
import sys
from AvalancheAPI import AvalancheAPI
import telegram
import time
#from dotenv import load_dotenv
#import os
#import threading

#load_dotenv()

#PATH_TO_CONFIG_JSON = os.environ['PATH_TO_CONFIG_JSON']

PATH_TO_DB = 'nochilltips.db' # name your database
SERVICE_FEE = 0.03 # this is a percentage.
TOKEN_ADDRESS = '' # contract address
MY_WALLET = '' # exchange's address
BUYS_ENABLED = True
TG_TOKEN_ID = '' # telegram bot's auth token. if blank, no tg alerts will be sent

def notify_arena(username, tipped, amount, hashIn, hashOut):
    message = 'Thanks @%s for %s AVAX, your %s NOCHILL has been sent.<br/>%s' % (username, tipped, amount, make_snowtrace_link(hashOut))
    message = message.replace('Thanks @None for ', 'Thanks Undetected Username for ')
    headers = {}
    headers['Content-Type'] = 'application/json'
    headers['Authorization'] = '' # bearer token - including the "Bearer " part

    payload = {}
    payload['content'] = message
    payload['files'] = []
    if float(tipped) >= 5.0:
        imageUrl = 'https://nochill.lol/buybot.jpg' # your buybot image if you want it, if not drop the if statement
        file = {"url":imageUrl,"isLoading":False, "fileType": "image"}
        payload['files'].append(file)
    payload['privacyType'] = 0
    r = requests.post('https://api.starsarena.com/threads', headers=headers, data=json.dumps(payload))

def notify_dev(message):
    if TG_TOKEN_ID != '':
        TOKEN=TG_TOKEN_ID # your telegram bot's auth token
        CHAT_ID='' # where your monitoring channel is
        if message != '':
            text = '%s' % (message)
            bot = telegram.Bot(token=TOKEN)
            bot.sendMessage(chat_id=CHAT_ID, text=text)

def notify_tg_group(message):
    if TG_TOKEN_ID != '':
        TOKEN=TG_TOKEN_ID # your telegram bot's auth token
        CHAT_ID='' # your public channel where it will say "user tipped x to nochillexchange"
        if message != '':
            text = '%s' % (message)
            bot = telegram.Bot(token=TOKEN)
            bot.sendMessage(chat_id=CHAT_ID, text=text)

def read_users_json():
    with open('users.json', 'r') as openfile: # users.json should exist in the same dir. this is a temporary fix to an arena problem.
        # Reading from json file
        json_object = json.load(openfile)

    return json_object

def get_username(conn, address):
    address = address.lower()
    username = get_username_from_db(conn, address)
    if username != None:
        return username
    else:
        username = address
        print(username)
        url = 'https://api.arenabook.xyz/user_info?user_address=eq.%s' % address
        r = requests.get(url)
        if r.status_code == 200:
            if len(r.json()) == 1:
                username = r.json()[0]['twitter_handle']
        print(username)
        if username != None:
            add_username_to_db(conn, address, username)
        else:
            try:
                users = read_users_json()
                if address.lower() in users:
                    username = users[address.lower()]
                else:
                    username = None
            except:
                pass
        return username

def get_username_from_db(conn, address):
    cur = conn.cursor()
    cur.execute("SELECT * FROM wallets WHERE wallet=?", (address,))

    rows = cur.fetchall()

    if len(rows) != 0:
        for row in rows:
            return row[2]
    else:
        return None

def add_username_to_db(conn, address, username):
    cur = conn.cursor()
    cur.execute("INSERT INTO wallets (wallet, username) VALUES(\"%s\",\"%s\");" % (address, username))
    conn.commit()
    return cur.lastrowid

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)

    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def check_transaction(conn, txnId):
    cur = conn.cursor()
    cur.execute("SELECT * FROM txn WHERE txnId=\"%s\";" % txnId)
    rows = cur.fetchall()
    if len(rows) > 0:
        return True
    else:
        return False

def add_transaction(conn, txnId, username):
    cur = conn.cursor()
    cur.execute("INSERT INTO txn (txnId, amountIn, tradeTxn, amountOut, transferTxn, username) VALUES(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");" % (txnId, 'x', 'x', 'x','x', username))
    conn.commit()
    return cur.lastrowid

def update_transaction_with_buy_data(conn, originTxn, amount, buy_txn):
    task = (amount, buy_txn, originTxn)
    sql = ''' UPDATE txn
              SET amountIn = ? ,
                  tradeTxn = ?
              WHERE txnId = ?'''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()

def make_snowtrace_link(txn):
    url = 'https://snowtrace.io/tx/%s?chainId=43114' % txn
    return url

def update_transaction_with_transfer_data(conn, originTxn, transferTxn, amount):
    task = (amount, transferTxn, originTxn)
    sql = ''' UPDATE txn
              SET amountOut = ? ,
                  transferTxn = ?
              WHERE txnId = ?'''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()

def update_transaction_with_user_data(conn, originTxn, username):
    task = (username, originTxn)
    sql = ''' UPDATE txn
              SET username = ?
              WHERE txnId = ?'''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()

def remove_transaction(conn, txnId):
    sql = 'DELETE FROM txn WHERE txnId=?'
    cur = conn.cursor()
    cur.execute(sql, (txnId,))
    conn.commit()

def get_transfers(address):
    url = 'https://api.routescan.io/v2/network/mainnet/evm/43114/etherscan/api?module=account&action=txlist&address=%s&startblock=0&endblock=99999999&page=1&offset=100&sort=desc&apikey=YourApiKeyToken' % address
    r = requests.get(url)
    print(r.status_code)
    transactions = []
    if r.status_code == 200:
        if r.json()['message'] == 'OK':
            for txn in r.json()['result']:
                # {'blockNumber': '39895801', 'timeStamp': '1704313821', 'hash': '0x23c2de1d272c168c4711a01ce65a229405b227ab4aca064d7d977cf6ec97ea03', 'nonce': '0', 'blockHash': '0x18280b7f315dc0c50d43ed110e4777bd08e6d84b92f875c3e20c87fcdb9d0c39', 'transactionIndex': '9', 'from': '0x9133dd7d4d62b190e4fa03398022dc2fb37ccfec', 'to': '0x167f0c5d8ef61a10b1f5829bd4c21126799737d0', 'value': '58717750000000000', 'gas': '21000', 'gasPrice': '25000000000', 'isError': '0', 'txreceipt_status': '1', 'input': '0x', 'contractAddress': '', 'cumulativeGasUsed': '674251', 'gasUsed': '21000', 'confirmations': '988386', 'methodId': '0x', 'functionName': ''}
                if txn['methodId'] == '0x' and txn['input'] == '0x':
                    if int(txn['value']) >= 10000000000000000: # minimum is 0.01
                        transactions.append(txn)
                    #print(txn)

    return transactions

payables = get_transfers(MY_WALLET)

#manual_missed_txn = {'hash': '0xe0bf3bd65cdf43975b63df4ad7ec0a0317548418c96265d359a63323dc1a0d7a',
# 'from': '0x0136E98f756d267e2c923049B362c193daaa5ad9',
# 'value': str(int(2.369* 10**18))}

#payables.append(manual_missed_txn)
#print(payables)
retry_transfers = []
if len(payables) != 0:
    conn = create_connection(PATH_TO_DB)
    avapi = AvalancheAPI()
    sql_create_txn_table = """ CREATE TABLE IF NOT EXISTS txn (
                                        id integer PRIMARY KEY,
                                        txnId text NOT NULL,
                                        amountIn text NOT NULL,
                                        tradeTxn text NOT NULL,
                                        amountOut text NOT NULL,
                                        transferTxn text NOT NULL,
                                        username text NOT NULL
                                    ); """

    sql_create_wallet_table = """ CREATE TABLE IF NOT EXISTS wallets (
                                        id integer PRIMARY KEY,
                                        wallet text NOT NULL,
                                        username text NOT NULL
                                    ); """

    sql_timestamp_table = """ CREATE TABLE IF NOT EXISTS timestamps (
                                        id integer PRIMARY KEY,
                                        txnId text NOT NULL,
                                        ts text NOT NULL
                                    ); """
    # create tables
    if conn is not None:
        # create tweets table
        create_table(conn, sql_create_txn_table)
        create_table(conn, sql_create_wallet_table)
        create_table(conn, sql_timestamp_table)
    else:
        print("Error! cannot create the database connection.")
        #notifySlack('Error! Cannot create the database connection!')
        #notifyDiscord('Error! Cannot create the database connection!')
        sys.exit(1)

    print('payables count: ',len(payables))
    for payable in payables:
        print('***************************************')
        if not check_transaction(conn, payable['hash']):
            time.sleep(5)
            # p is already in 10**18 format
            payable_value_readable = int(payable['value'])/10**18
            p = int(payable['value'])
            print(payable_value_readable)
            p = p * (1-SERVICE_FEE)
            p = int(p)

            # get the username
            username = get_username(conn, payable['from'])
            notify_dev('1/3 got a transaction from %s - %s avax - hash: %s' % (username, int(payable['value'])/10**18, make_snowtrace_link(payable['hash'])))
            add_transaction(conn, payable['hash'], username)
            if BUYS_ENABLED == True:
                amt = None
                buy_success = False
                buy_txn_id = None
                try:
                    amt, buy_success, buy_txn_id = avapi.buy(TOKEN_ADDRESS, p)
                    print(amt)
                    print(buy_success)
                    print(buy_txn_id)
                except:
                    remove_transaction(conn, payable['hash'])
                    buy_success = False
                    msg = 'Buy failed for incoming transaction %s from user %s. It has been removed from the db and will be retried shortly.' % (payable['hash'], username)
                    print(msg)
                    notify_dev(msg)

                if buy_success == True: # Check if the transaction went through
                    print('bought successfully!')
                    notify_dev('2/3 purchased %s NOCHILL - hash: %s' % (int(amt)/10**18, make_snowtrace_link(buy_txn_id)))
                    update_transaction_with_buy_data(conn, payable['hash'], payable_value_readable, buy_txn_id)
                    print('transfer %s nochill to %s' % (int(amt)/10**18,payable['from']))
                    time.sleep(20)
                    try:
                        transferTxn = avapi.transfer(TOKEN_ADDRESS, payable['from'], amt)
                        if transferTxn != 'None':
                            notify_dev('3/3 transferred %s NOCHILL - hash: %s' % (int(amt)/10**18, make_snowtrace_link(transferTxn)))
                            update_transaction_with_transfer_data(conn, payable['hash'], transferTxn, int(amt)/10**18)
                            notify_arena(username, int(payable['value'])/10**18, int(amt)/10**18, payable['hash'], transferTxn)
                            notify_tg_group('%s tipped %s to nochillexchange' % (username, payable_value_readable))
                        else:
                            xfer = {}
                            xfer['amount'] = amt
                            xfer['to'] = payable['from']
                            xfer['username'] = username
                            xfer['amount_readable'] = int(amt)/10**18
                            xfer['hash'] = payable['hash']
                            xfer['incoming'] = int(payable['value'])/10**18
                            retry_transfers.append(xfer)
                            notify_dev('transfer failed. added to retry list.')
                    except:
                        xfer = {}
                        xfer['amount'] = amt
                        xfer['to'] = payable['from']
                        xfer['username'] = username
                        xfer['amount_readable'] = int(amt)/10**18
                        xfer['hash'] = payable['hash']
                        xfer['incoming'] = int(payable['value'])/10**18
                        retry_transfers.append(xfer)
                        notify_dev('transfer failed. added to retry list.')
                else:
                    remove_transaction(conn, payable['hash'])
                    buy_success = False
                    msg = 'Buy failed for incoming transaction %s from user %s. It has been removed from the db and will be retried shortly.' % (payable['hash'], username)
                    print(msg)
                    notify_dev(msg)
            else:
                #amt = 9220898495277172785152
                avapi.transfer(TOKEN_ADDRESS, payable['from'], amt)
                print('would have transferred for %s' % payable['hash'])
                add_transaction(conn, payable['hash'])
        else:
            print('skipped for %s - %s' % (get_username(conn, payable['from']), payable['hash']))
            #update_transaction_with_user_data(conn, payable['hash'], get_username(payable['from']))

if len(retry_transfers) != 0:
    time.sleep(30)
    avapi = AvalancheAPI()
    for xfer in retry_transfers:
        try:
            transferTxn = avapi.transfer(TOKEN_ADDRESS, xfer['to'], xfer['amount'])
            if transferTxn != 'None':
                notify_dev('[retry] 3/3 transferred %s NOCHILL - hash: %s' % (xfer['amount_readable'], make_snowtrace_link(transferTxn)))
                update_transaction_with_transfer_data(conn, xfer['hash'], transferTxn, xfer['amount_readable'])
                notify_arena(xfer['username'], xfer['incoming'], xfer['amount_readable'], xfer['hash'], transferTxn)
                notify_tg_group('%s tipped %s to nochillexchange' % (xfer['username'], xfer['incoming']))
            else:
                notify_dev('transfer failed again. not retrying. please manually tip %s NOCHILL amount %s and update db. wallet: %s' % (xfer['username'], xfer['amount_readable'], xfer['to']))
            time.sleep(30)
        except:
            notify_dev('transfer failed again. not retrying. please manually tip %s NOCHILL amount %s and update db. wallet: %s' % (xfer['username'], xfer['amount_readable'], xfer['to']))
