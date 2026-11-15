#!/usr/bin/env python3

# add import
import time
from web3 import Web3

# add definition
Local_Ethereum_Endpoint = 'http://10.83.2.226:8545/634f526d-2803-4283-9ca9-984d687f7d9c'
Setup_Address = '0x6BD46722677Ecc4D15d450E89283896EcA92f79E'
Attack_Address = '0x76d5d8B7B3aa9455ae80D471F4B07e21ECb6CBf8'
w3 = Web3(Web3.HTTPProvider(Local_Ethereum_Endpoint, request_kwargs={'timeout': 15}))

# contract ABI
setup_abi = [
    {'inputs': [], 'name': 'isSolved', 'outputs': [{'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [], 'name': 'TARGET', 'outputs': [{'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}
]
attack_abi = [
    {'inputs': [], 'name': 'legendaryCount', 'outputs': [{'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}
]

setup = w3.eth.contract(address=Web3.to_checksum_address(Setup_Address), abi=setup_abi)
attack = w3.eth.contract(address=Web3.to_checksum_address(Attack_Address), abi=attack_abi)

# check the already deployed attack contract
error_count = 0
while True:
    try:
        if not w3.is_connected():
            raise ConnectionError('RPC unavailable')
        count = attack.functions.legendaryCount().call()
        solved = setup.functions.isSolved().call()
        print('Legendary:', str(count) + '/2', 'Solved:', solved)
        if solved:
            print('CHALLENGE SOLVED!')
            print('Connect with nc and choose 3')
            break
        error_count = 0
        time.sleep(3)
    except KeyboardInterrupt:
        print('Stopped')
        break
    except Exception as error:
        error_count += 1
        print('RPC error', error_count, ':', error)
        if error_count >= 30:
            print('RPC unavailable after 30 retries')
            break
        time.sleep(5)
