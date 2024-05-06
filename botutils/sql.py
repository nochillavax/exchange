import sqlite3
from sqlite3 import Error
import sys

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

def add_transaction(conn, txnId, amountIn, username):
    cur = conn.cursor()
    cur.execute("INSERT INTO txn (txnId, amountIn, tradeTxn, amountOut, transferTxn, username) VALUES(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");" % (txnId, amountIn, 'x', 'x','x', username))
    conn.commit()
    return cur.lastrowid

def update_transaction_with_buy_data(conn, originTxn, amount, buy_txn, amountOut):
    task = (amount, buy_txn, amountOut, originTxn)
    sql = ''' UPDATE txn
              SET amountIn = ? ,
                  tradeTxn = ? ,
                  amountOut = ?
              WHERE txnId = ?'''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()

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

def update_transaction_with_amount(conn, originTxn, amount):
    task = (amount, originTxn)
    sql = ''' UPDATE txn
              SET amountIn = ?
              WHERE txnId = ?'''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()

def get_txns(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM txn")

    rows = cur.fetchall()

    all_txns = []

    if len(rows) != 0:
        for row in rows:
            tx = {}
            tx['hash'] = row[1]
            tx['amt'] = row[2]
            tx['user'] = row[6]
            tx['nochill'] = row[4]
            #print(tx)
            all_txns.append(tx)
        return all_txns
    else:
        return None

def get_wallet(conn, username):
    cur = conn.cursor()
    cur.execute("SELECT * FROM wallets WHERE username=?", (username,))

    rows = cur.fetchall()

    if len(rows) != 0:
        for row in rows:
            return row[1]
    else:
        return None

def get_waiting_transfers(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM txn WHERE transferTxn='x' AND amountOut != 'x';")
    rows = cur.fetchall()
    payables = []
    for row in rows:
        xfer = {}
        xfer['amount'] = int(float(row[4])*10**18)
        xfer['to'] = get_wallet(conn, row[6])
        xfer['username'] = row[6]
        xfer['amount_readable'] = row[4]
        xfer['hash'] = row[1]
        xfer['incoming'] = float(row[2])
        payables.append(xfer)

    return payables

def get_pending_transfers(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM txn WHERE transferTxn='pending' AND amountOut != 'x';")
    rows = cur.fetchall()
    payables = []
    for row in rows:
        xfer = {}
        xfer['amount'] = int(float(row[4])*10**18)
        xfer['to'] = get_wallet(conn, row[6])
        xfer['username'] = row[6]
        xfer['amount_readable'] = row[4]
        xfer['hash'] = row[1]
        xfer['incoming'] = float(row[2])
        payables.append(xfer)

    return payables

def update_transfer_to_pending(conn, blockhash):
    task = ('pending', blockhash)
    sql = ''' UPDATE txn
              SET transferTxn = ?
              WHERE txnId = ?'''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()

def update_transfer_to_waiting(conn, blockhash):
    task = ('x', blockhash)
    sql = ''' UPDATE txn
              SET transferTxn = ?
              WHERE txnId = ?'''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()

def create_tables(conn):
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
