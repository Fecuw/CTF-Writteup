#!/usr/bin/env python3
import json
import math
import time
from web3 import Web3
from eth_account import Account

# add definition
Local_Ethereum_Endpoint = 'http://10.83.2.26:8545/d3e96c84-bc6e-4656-9ef0-4d9ae9124078'
private_key = '0xd48a6d74a3442118cbfc6cbde38956481229b966236d84baa4dbaf379cb8020d'
setup_address = '0xE25664Ee5875D6916D4Acb70a8019905ade88d56'

w3 = Web3(Web3.HTTPProvider(Local_Ethereum_Endpoint))
account = Account.from_key(private_key)

# ABI definitions (only functions used here)
setup_abi = [
    {"inputs": [], "name": "TARGET", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "isSolved", "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"}
]
chal_abi = [
    {"inputs": [{"name": "key", "type": "bytes32"}], "name": "restoreFiles", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "keyHash", "outputs": [{"type": "bytes32"}], "stateMutability": "view", "type": "function"}
]

# read bytes variable from Solidity storage
# short bytes are stored in the slot itself
# long bytes are stored from keccak256(slot)
def read_bytes(address, slot):
    data = bytes(w3.eth.get_storage_at(address, slot))
    num = int.from_bytes(data, 'big')
    if num % 2 == 0:
        size = (num & 255) // 2
        return data[:size]

    size = num // 2
    start = int.from_bytes(Web3.keccak(slot.to_bytes(32, 'big')), 'big')
    result = b''
    for i in range(math.ceil(size / 32)):
        result += bytes(w3.eth.get_storage_at(address, (start + i) % (2 ** 256)))
    return result[:size]


print('Connecting...')
if not w3.is_connected():
    raise Exception('RPC connection failed')

setup = w3.eth.contract(address=Web3.to_checksum_address(setup_address), abi=setup_abi)
chal_address = setup.functions.TARGET().call()
chal = w3.eth.contract(address=Web3.to_checksum_address(chal_address), abi=chal_abi)
print('Chal:', chal_address)

if setup.functions.isSolved().call():
    print('Already solved')
else:
    # slot 0 = n, 1 = e, 2 = d, 3 = ciphertext
    n = int.from_bytes(read_bytes(chal_address, 0), 'big')
    e = int.from_bytes(read_bytes(chal_address, 1), 'big')
    d = int.from_bytes(read_bytes(chal_address, 2), 'big')
    c = int.from_bytes(read_bytes(chal_address, 3), 'big')

    print('n bits:', n.bit_length())
    print('e:', e)
    print('d bits:', d.bit_length())

    # RSA decrypt
    m = pow(c, d, n)
    aes_key = m.to_bytes(32, 'big')
    print('AES key:', aes_key.hex())

    # check key hash
    key_hash = bytes(chal.functions.keyHash().call())
    my_hash = bytes(Web3.keccak(aes_key))
    print('Hash OK:', key_hash == my_hash)
    if key_hash != my_hash:
        raise Exception('Wrong AES key')

    # send restoreFiles transaction
    nonce = w3.eth.get_transaction_count(account.address)
    tx = chal.functions.restoreFiles(aes_key).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'chainId': w3.eth.chain_id,
        'gas': 200000,
        'gasPrice': w3.eth.gas_price
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print('TX:', tx_hash.hex())
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    print('TX status:', receipt.status)
    print('Solved:', setup.functions.isSolved().call())
    print('Get flag: nc 10.83.2.26 31337 -> 3')
