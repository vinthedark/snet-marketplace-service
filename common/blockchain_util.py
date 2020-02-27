import json
import uuid
from enum import Enum

import web3
from eth_account.messages import defunct_hash_message

from web3 import Web3

from common.logger import get_logger

logger = get_logger(__name__)

class ContractType(Enum):
    REGISTRY = "REGISTRY"
    MPE = "MPE"
    RFAI = "RFAI"


class BlockChainUtil(object):

    def __init__(self, provider_type, provider):
        if provider_type == "HTTP_PROVIDER":
            self.provider = Web3.HTTPProvider(provider)
        elif provider_type == "WS_PROVIDER":
            self.provider = web3.providers.WebsocketProvider(provider)
        else:
            raise Exception("Only HTTP_PROVIDER and WS_PROVIDER provider type are supported.")
        self.web3_object = Web3(self.provider)

    def load_contract(self, path):
        with open(path) as f:
            contract = json.load(f)
        return contract

    def read_contract_address(self, net_id, path, key):
        contract = self.load_contract(path)
        return Web3.toChecksumAddress(contract[str(net_id)][key])

    def contract_instance(self, contract_abi, address):
        return self.web3_object.eth.contract(abi=contract_abi, address=address)

    def get_contract_instance(self, base_path, contract_name, net_id):
        contract_network_path, contract_abi_path = self.get_contract_file_paths(base_path, contract_name)

        contract_address = self.read_contract_address(net_id=net_id, path=contract_network_path,
                                                      key='address')
        contract_abi = self.load_contract(contract_abi_path)
        logger.debug(f"contract address is {contract_address}")
        contract_instance = self.contract_instance(contract_abi=contract_abi, address=contract_address)

        return contract_instance

    def generate_signature(self, data_types, values, signer_key):
        signer_key = "0x" + signer_key if not signer_key.startswith("0x") else signer_key
        message = web3.Web3.soliditySha3(data_types, values)
        signature = self.web3_object.eth.account.signHash(defunct_hash_message(message), signer_key)
        return signature.signature.hex()

    def generate_signature_bytes(self, data_types, values, signer_key):
        signer_key = "0x" + signer_key if not signer_key.startswith("0x") else signer_key
        message = web3.Web3.soliditySha3(data_types, values)
        signature = self.web3_object.eth.account.signHash(defunct_hash_message(message), signer_key)
        return bytes(signature.signature)

    def get_nonce(self, address):
        """ transaction count includes pending transaction also. """
        nonce = self.web3_object.eth.getTransactionCount(address)
        return nonce

    def sign_transaction_with_private_key(self, private_key, transaction_object):
        return self.web3_object.eth.account.signTransaction(transaction_object, private_key).rawTransaction

    def create_transaction_object(self, *positional_inputs, method_name, address, contract_path, contract_address_path,
                                  net_id):
        nonce = self.get_nonce(address=address)
        self.contract = self.load_contract(path=contract_path)
        self.contract_address = self.read_contract_address(net_id=net_id, path=contract_address_path, key='address')
        self.contract_instance = self.contract_instance(contract_abi=self.contract, address=self.contract_address)
        print("gas_price == ", self.web3_object.eth.gasPrice)
        print("nonce == ", nonce)
        gas_price = 3 * (self.web3_object.eth.gasPrice)
        transaction_object = getattr(self.contract_instance.functions, method_name)(
            *positional_inputs).buildTransaction({
            "from": address,
            "nonce": nonce,
            "gasPrice": gas_price,
            "chainId": net_id
        })
        return transaction_object

    def process_raw_transaction(self, raw_transaction):
        return self.web3_object.eth.sendRawTransaction(raw_transaction).hex()

    def create_account(self):
        account = self.web3_object.eth.account.create(uuid.uuid4().hex)
        return account.address, account.privateKey.hex()

    def get_current_block_no(self):
        return self.web3_object.eth.blockNumber

    def get_transaction_receipt_from_blockchain(self, transaction_hash):
        return self.web3_object.eth.getTransactionReceipt(transaction_hash)

    def get_contract_file_paths(self, base_path, contract_name):
        if contract_name == ContractType.REGISTRY.value:
            json_file = "Registry.json"
        elif contract_name == ContractType.MPE.value:
            json_file = "MultiPartyEscrow.json"
        elif contract_name == ContractType.RFAI.value:
            json_file = "ServiceRequest.json"

        else:
            raise Exception("Invalid contract Type {}".format(contract_name))

        contract_network_path = base_path + "/{}/{}".format("networks", json_file)
        contract_abi_path = base_path + "/{}/{}".format("abi", json_file)

        return contract_network_path, contract_abi_path
