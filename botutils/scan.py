import requests
import json

def get_transfers(api_key, address):
    url = 'https://api.snowscan.xyz/api?module=account&action=txlist&address=%s&startblock=0&endblock=99999999&page=1&offset=1000&sort=desc&apikey=%s' % (address, api_key)
    r = requests.get(url)
    print(r.status_code)
    transactions = []
    if r.status_code == 200:
        if r.json()['message'] == 'OK':
            for txn in r.json()['result']:
                # {'blockNumber': '39895801', 'timeStamp': '1704313821', 'hash': '0x23c2de1d272c168c4711a01ce65a229405b227ab4aca064d7d977cf6ec97ea03', 'nonce': '0', 'blockHash': '0x18280b7f315dc0c50d43ed110e4777bd08e6d84b92f875c3e20c87fcdb9d0c39', 'transactionIndex': '9', 'from': '0x9133dd7d4d62b190e4fa03398022dc2fb37ccfec', 'to': '0x167f0c5d8ef61a10b1f5829bd4c21126799737d0', 'value': '58717750000000000', 'gas': '21000', 'gasPrice': '25000000000', 'isError': '0', 'txreceipt_status': '1', 'input': '0x', 'contractAddress': '', 'cumulativeGasUsed': '674251', 'gasUsed': '21000', 'confirmations': '988386', 'methodId': '0x', 'functionName': ''}
                if txn['methodId'] == '0x' and txn['input'] == '0x':
                    if int(txn['value']) >= 10000000000000000:
                        transactions.append(txn)
                    #print(txn)

    return transactions

def make_explorer_link(txn):
    url = 'https://snowscan.xyz/tx/%s' % txn
    #url = 'https://snowtrace.io/tx/%s?chainId=43114' % txn
    return url
