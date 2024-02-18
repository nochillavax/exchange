# -------------------------------- LIBRARIES -------------------------------- #
from web3 import Web3
from web3.middleware import geth_poa_middleware
import AvalancheConfig as config
import time
import json

TRADE_PAIR_ROUTE_1 = "0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7" # CA FOR WAVAX
TRADE_PAIR_ROUTE_2 = "0xAcFb898Cff266E53278cC0124fC2C7C94C8cB9a5" # CA FOR NOCHILL
ABI_FILE = 'nochillabi.json'

# ------------------------------- MAIN CLASS -------------------------------- #
class AvalancheAPI(object):
# ------------------------------- INITIALIZE -------------------------------- #
    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(config.RPC_URL))
        self.spend = self.web3.to_checksum_address(config.WAVAX_ADDRESS)
        config.SENDER_ADDRESS = self.web3.to_checksum_address(config.SENDER_ADDRESS)
        self.start_balance = self.getBalance()
        self.contract = self.web3.eth.contract(address=self.web3.to_checksum_address(config.ROUTER_CONTRACT_ADDRESS), abi=config.AVA_ABI)
        #self.quote = self.web3.eth.contract(address=self.web3.to_checksum_address(config.QUOTER_CONTRACT_ADDRESS), abi=config.QUOTE_ABI)
        print('Starting Balance (AVAX): ', self.start_balance)
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)


# ---------------------------------- UTILS ---------------------------------- #
    def getBalance(self):  # Get AVAX balance
        return self.web3.from_wei(self.web3.eth.get_balance(config.SENDER_ADDRESS), 'ether')

    def getNonce(self):  # Get address nonce
        return self.web3.eth.get_transaction_count(config.SENDER_ADDRESS)

    def get_token_info(self, token_address): # Get symbol and decimal count from contract address
        contract_id = self.web3.to_checksum_address(token_address)
        sell_token_contract = self.web3.eth.contract(contract_id, abi=config.AVA_ABI)
        symbol = sell_token_contract.functions.symbol().call()
        decimals = sell_token_contract.functions.decimals().call()
        return symbol, decimals

    def get_token_holdings(self, token_address): # Get amount of tokens hold and value(in AVAX) of these tokens
        contract_id = self.web3.to_checksum_address(token_address)
        sell_token_contract = self.web3.eth.contract(contract_id, abi=config.AVA_ABI)

        balance = sell_token_contract.functions.balanceOf(config.SENDER_ADDRESS).call()  # How many tokens do we have?
        value = self.contract.functions.getAmountsOut(balance,
                                                      [self.web3.to_checksum_address(token_address),
                                                       self.web3.to_checksum_address(config.WAVAX_ADDRESS)]).call()
        return balance, value[1]

# ----------------------------------- BUY ----------------------------------- #
    def buy(self, token_address, token_to_spend):
        token_to_buy = self.web3.to_checksum_address(token_address)
        # determine how much we'll get
        print(token_to_spend)
        #token_to_spend_uint = self.web3.from_wei(token_to_spend, 'ether')

        #quote = self.quote.functions.findBestPathFromAmountIn(
        #    [token_to_buy, self.web3.to_checksum_address(config.WAVAX_ADDRESS)],
        #    token_to_spend
        #)

        x= self.contract.functions.getAmountsOut(
            token_to_spend,
            [self.web3.to_checksum_address(config.WAVAX_ADDRESS),token_to_buy],
        ).call()
        print(x)
        print('amount of avax: ', x[0]/10**18)
        print('amount of nochill: ', x[1]/10**18)
        x[1] = int(x[1] * 0.98)

        #print(quote)
        #sys.exit(1)
        print((int(time.time()) + 10000))

        txn = self.contract.functions.swapAVAXForExactTokens(
            x[1],
            [
              str(self.web3.to_checksum_address(TRADE_PAIR_ROUTE_1)),
              str(self.web3.to_checksum_address(TRADE_PAIR_ROUTE_2))
            ],
            self.web3.to_checksum_address(config.SENDER_ADDRESS),  # Our own (metamask) wallet address
            (int(time.time()) + 10000)  # Deadline
        ).build_transaction({
            'from': config.SENDER_ADDRESS,
            'value': x[0],
            'gas': 200000,
            'gasPrice': self.web3.to_wei('100', 'gwei'),  # minimum is 85 gwei
            'nonce': self.web3.eth.get_transaction_count(config.SENDER_ADDRESS),
        })

        signed_txn = self.web3.eth.account.sign_transaction(txn, private_key=config.PRIVATE_KEY)
        tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx = self.web3.to_hex(tx_token)
        print('Buy Transaction: %s' % tx)
        txn_receipt = self.awaitReceipt(tx_token) # Wait for transaction to finish
        print(txn_receipt)
        if txn_receipt.status == 1:
            return x[1], True, tx
        else:
            return x[1], False, tx

    def transfer(self, contract, to, value):
        # temporary
        #to = '0x167f0c5D8ef61A10B1f5829bd4C21126799737D0'
        with open(ABI_FILE) as abi_file:
            contract_abi = json.load(abi_file)
        contract = self.web3.eth.contract(address=contract, abi=contract_abi)
        to = self.web3.to_checksum_address(to)
        # Define transaction details
        #print(value)
        #token_amount = self.web3.to_wei(value, 'ether')  # Adjust the amount as needed
        #print(token_amount)
        #sys.exit(1)
        # Get the nonce for the transaction
        nonce = self.web3.eth.get_transaction_count(config.SENDER_ADDRESS)

        # Build the transaction
        transaction = contract.functions.transfer(to, value).build_transaction({
            'gas': 200000,  # Adjust the gas limit as needed
            'nonce': nonce,
        })

        # Sign the transaction with the private key
        signed_txn = self.web3.eth.account.sign_transaction(transaction, config.PRIVATE_KEY)

        # Attempt to send the transaction
        tx_hash_notify = 'None'
        try:
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Transaction sent! Hash: {tx_hash.hex()}")
            tx_hash_notify = str(tx_hash.hex())
        except Exception as e:
            print(f"Error sending transaction: {e}")

        return tx_hash_notify

    def buy_token(self):
        self.quantity = Decimal(self.quantity) * (10**18)
        txn = self.swapper.functions.fromETHtoToken(
            self.address,
            self.token_address,
            self.slippage
        ).buildTransaction(
            {'from': self.address,
            'gas': 5800000,
            'gasPrice': self.gas_price,
            'nonce': self.w3.eth.getTransactionCount(self.address),
            'value': int(self.quantity)}
            )
        txn.update({ 'gas' : int(self.estimateGas(txn))})
        signed_txn = self.w3.eth.account.sign_transaction(
            txn,
            self.private_key
        )
        txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        print(style.GREEN + "\nBUY Hash:",txn.hex() + style.RESET)
        txn_receipt = self.w3.eth.waitForTransactionReceipt(txn)
        if txn_receipt["status"] == 1: return True,style.GREEN +"\nBUY Transaction Successfull!" + style.RESET
        else: return False, style.RED +"\nBUY Transaction Faild!" + style.RESET

    def estimateGas(self, txn):
        gas = self.w3.eth.estimateGas({
                    "from": txn['from'],
                    "to": txn['to'],
                    "value": txn['value'],
                    "data": txn['data']})
        gas = gas + (gas / 10) # Adding 1/10 from gas to gas!
        maxGasAVAX = Web3.from_wei(gas * self.gas_price, "ether")
        print(style.GREEN + "\nMax Transaction cost " + str(maxGasAVAX) + " AVAX" + style.RESET)

        if maxGasAVAX > self.MaxGasInAVAX:
            print(style.RED +"\nTx cost exceeds your settings, exiting!")
            raise SystemExit
        return gas

# ---------------------------- WAIT FOR RECEIPT ----------------------------- #
    def awaitReceipt(self, tx):
        try:
            return self.web3.eth.wait_for_transaction_receipt(tx, timeout=30)
        except Exception as ex:
            print('Failed to wait for receipt: ', ex)
            return None
"""
# --------------------------------- APPROVE --------------------------------- #
    def approve(self, token_address):
        contract_id = self.web3.to_checksum_address(token_address)
        sellTokenContract = self.web3.eth.contract(contract_id, abi=config.AVA_ABI)
        approve = sellTokenContract.functions.approve(self.web3.to_checksum_address(config.PANGOLIN_ROUTER_CONTRACT_ADDRESS), 2 ** 256 - 1).buildTransaction({
            'from': self.web3.to_checksum_address(config.SENDER_ADDRESS),
            'nonce': self.web3.eth.get_transaction_count(config.SENDER_ADDRESS),
        })
        signed_txn = self.web3.eth.account.sign_transaction(approve, private_key=config.PRIVATE_KEY)
        tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx = self.web3.toHex(tx_token)
        return tx

# ----------------------------------- SELL ---------------------------------- #
    def sell(self, token_address, sell_prcnt=100):
        balance, value = self.get_token_holdings(token_address)
        sell_amt = int(balance * sell_prcnt/100)

        # return
        txn = self.contract.functions.swapExactTokensForAVAXSupportingFeeOnTransferTokens(
            sell_amt,
            1,  # Front-running risk, potential to lose all your money, keep that in mind
            [self.web3.to_checksum_address(token_address), self.spend],
            config.SENDER_ADDRESS,
            int(time.time()) + 10000
        ).buildTransaction({
            'from': config.SENDER_ADDRESS,
            'gas': 200000,
            'gasPrice': self.web3.toWei('100', 'gwei'),
            'nonce': self.web3.eth.get_transaction_count(config.SENDER_ADDRESS),
        })

        signed_txn = self.web3.eth.account.sign_transaction(txn, private_key=config.PRIVATE_KEY)
        tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx = self.web3.toHex(tx_token)
        return tx
"""
