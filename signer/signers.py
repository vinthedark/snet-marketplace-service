import json
from urllib.parse import urlparse

import boto3
import grpc
import web3
from eth_account.messages import defunct_hash_message
from web3 import Web3

from common.blockchain_util import BlockChainUtil
from common.logger import get_logger
from common.utils import Utils
from signer.config import GET_SERVICE_DETAILS_FOR_GIVEN_ORG_ID_AND_SERVICE_ID_ARN, METERING_ARN, NETWORKS, \
    PREFIX_FREE_CALL, REGION_NAME, SIGNER_ADDRESS, SIGNER_KEY
from signer.constant import MPE_ADDR_PATH
from signer.stubs import state_service_pb2, state_service_pb2_grpc

logger = get_logger(__name__)

FREE_CALL_EXPIRY=172800

class Signer:
    def __init__(self, net_id):
        self.net_id = net_id
        self.lambda_client = boto3.client("lambda", region_name=REGION_NAME)
        self.obj_utils = Utils()
        self.obj_blockchain_utils = BlockChainUtil(
            provider_type="HTTP_PROVIDER",
            provider=NETWORKS[self.net_id]["http_provider"],
        )
        self.mpe_address = self.obj_blockchain_utils.read_contract_address(
            net_id=self.net_id, path=MPE_ADDR_PATH, key="address")
        self.current_block_no = self.obj_blockchain_utils.get_current_block_no(
        )

    def _get_free_calls_allowed(self, org_id, service_id, group_id):
        lambda_payload = {
            "httpMethod": "GET",
            "pathParameters": {
                "orgId": org_id,
                "serviceId": service_id
            },
        }
        response = self.lambda_client.invoke(
            FunctionName=GET_SERVICE_DETAILS_FOR_GIVEN_ORG_ID_AND_SERVICE_ID_ARN,
            InvocationType="RequestResponse",
            Payload=json.dumps(lambda_payload),
        )
        response_body_raw = json.loads(response.get("Payload").read())["body"]
        get_service_response = json.loads(response_body_raw)
        if get_service_response["status"] == "success":
            groups_data = get_service_response["data"].get("groups", [])
            for group_data in groups_data:
                if group_data["group_id"] == group_id:
                    return group_data["free_calls"]
        raise Exception("Unable to fetch free calls information for service %s under organization %s for %s group.",
                        service_id, org_id, group_id)

    def _get_total_calls_made(self, username, org_id, service_id, group_id):
        lambda_payload = {
            "httpMethod": "GET",
            "queryStringParameters": {
                "organization_id": org_id,
                "service_id": service_id,
                "username": username,
                "group_id": group_id,
            },
        }
        response = self.lambda_client.invoke(
            FunctionName=METERING_ARN,
            InvocationType="RequestResponse",
            Payload=json.dumps(lambda_payload),
        )
        if response["StatusCode"] == 200:
            metering_data_raw = json.loads(response.get("Payload").read())["body"]
            total_calls_made = json.loads(metering_data_raw).get("total_calls_made", None)
            if total_calls_made is not None:
                return total_calls_made
        raise Exception("Unable to fetch total calls made for service %s under organization %s for %s group.",
                        service_id, org_id, group_id)

    def _free_calls_allowed(self, username, org_id, service_id, group_id):
        """
            Method to check free calls exists for given user or not.
            Call monitoring service to get the details
        """
        free_calls_allowed = self._get_free_calls_allowed(org_id, service_id, group_id)
        total_calls_made = self._get_total_calls_made(username, org_id, service_id, group_id)
        is_free_calls_allowed = (True if ((free_calls_allowed - total_calls_made) > 0) else False)
        return is_free_calls_allowed

    def signature_for_free_call(self, user_data, org_id, service_id, group_id):
        """
            Method to generate signature for free call.
        """
        try:
            username = user_data["authorizer"]["claims"]["email"]
            if self._free_calls_allowed(
                username=username, org_id=org_id, service_id=service_id, group_id=group_id):
                current_block_no = self.obj_utils.get_current_block_no(
                    ws_provider=NETWORKS[self.net_id]["ws_provider"])
                provider = Web3.HTTPProvider(
                    NETWORKS[self.net_id]["http_provider"])
                w3 = Web3(provider)
                message = web3.Web3.soliditySha3(
                    ["string", "string", "string", "string", "uint256"],
                    [
                        PREFIX_FREE_CALL, username, org_id, service_id,
                        current_block_no
                    ],
                )
                signer_key = SIGNER_KEY
                if not signer_key.startswith("0x"):
                    signer_key = "0x" + signer_key
                signature = bytes(
                    w3.eth.account.signHash(defunct_hash_message(message),
                                            signer_key).signature)
                signature = signature.hex()
                if not signature.startswith("0x"):
                    signature = "0x" + signature
                return {
                    "snet-free-call-user-id": username,
                    "snet-payment-channel-signature-bin": signature,
                    "snet-current-block-number": current_block_no,
                    "snet-payment-type": "free-call",
                    "snet-free-call-auth-token-bin":"",
                    "snet-free-call-token-expiry-block":0
                }
            else:
                raise Exception("Free calls expired for username %s.",
                                username)
        except Exception as e:
            logger.error(repr(e))
            raise e

    def signature_for_regular_call(self, user_data, channel_id, nonce, amount):
        """
            Method to generate signature for regular call.
        """
        try:
            username = user_data["authorizer"]["claims"]["email"]
            data_types = ["string", "address", "uint256", "uint256", "uint256"]
            values = [
                "__MPE_claim_message",
                self.mpe_address,
                channel_id,
                nonce,
                amount,
            ]
            signature = self.obj_blockchain_utils.generate_signature(
                data_types=data_types, values=values, signer_key=SIGNER_KEY)
            return {
                "snet-payment-channel-signature-bin": signature,
                "snet-payment-type": "escrow",
                "snet-payment-channel-id": channel_id,
                "snet-payment-channel-nonce": nonce,
                "snet-payment-channel-amount": amount,
                "snet-current-block-number": self.current_block_no,
            }
        except Exception as e:
            logger.error(repr(e))
            raise Exception(
                "Unable to generate signature for daemon call for username %s",
                username)

    def signature_for_state_service(self, user_data, channel_id):
        """
            Method to generate signature for state service.
        """
        try:
            username = user_data["authorizer"]["claims"]["email"]
            data_types = ["string", "address", "uint256", "uint256"]
            values = [
                "__get_channel_state",
                self.mpe_address,
                channel_id,
                self.current_block_no,
            ]
            signature = self.obj_blockchain_utils.generate_signature(
                data_types=data_types, values=values, signer_key=SIGNER_KEY)
            return {
                "signature": signature,
                "snet-current-block-number": self.current_block_no,
            }
        except Exception as e:
            logger.error(repr(e))
            raise Exception(
                "Unable to generate signature for daemon call for username %s",
                username)

    def signature_for_open_channel_for_third_party(self, recipient, group_id, amount_in_cogs, expiration, message_nonce,
                                                   sender_private_key, executor_wallet_address):
        data_types = ["string", "address", "address", "address", "address", "bytes32", "uint256", "uint256",
                      "uint256"]
        values = ["__openChannelByThirdParty", self.mpe_address, executor_wallet_address, SIGNER_ADDRESS, recipient,
                  group_id, amount_in_cogs, expiration, message_nonce]
        signature = self.obj_blockchain_utils.generate_signature(data_types=data_types, values=values,
                                                                 signer_key=sender_private_key)
        v, r, s = Web3.toInt(hexstr="0x" + signature[-2:]), signature[:66], "0x" + signature[66:130]
        return {"r": r, "s": s, "v": v, "signature": signature}

    def _is_free_call_available(self, email, token_for_free_call, expiry_date_block, signature,
                               current_block_number,daemon_endpoint):

        request = state_service_pb2.FreeCallStateRequest()
        request.user_id = email
        request.token_for_free_call = token_for_free_call
        request.token_expiry_date_block = expiry_date_block
        request.signature = signature
        request.current_block = current_block_number

        endpoint_object = urlparse(daemon_endpoint)
        if endpoint_object.port is not None:
            channel_endpoint = endpoint_object.hostname + ":" + str(endpoint_object.port)
        else:
            channel_endpoint = endpoint_object.hostname

        if endpoint_object.scheme == "http":
            channel = grpc.insecure_channel(channel_endpoint)
        elif endpoint_object.scheme == "https":
            channel = grpc.secure_channel(channel_endpoint, grpc.ssl_channel_credentials())
        else:
            raise ValueError('Unsupported scheme in service metadata ("{}")'.format(endpoint_object.scheme))

        stub = state_service_pb2_grpc.FreeCallStateServiceStub(channel)
        response = stub.GetFreeCallsAvailable(request)
        if response.free_calls_available >0:
            return True
        return False


    def _get_daemon_endpoint_for_group(self,org_id,service_id,group_id):
        lambda_payload = {
            "httpMethod": "GET",
            "pathParameters": {
                "orgId": org_id,
                "serviceId": service_id
            },
        }
        response = self.lambda_client.invoke(
            FunctionName=GET_SERVICE_DETAILS_FOR_GIVEN_ORG_ID_AND_SERVICE_ID_ARN,
            InvocationType="RequestResponse",
            Payload=json.dumps(lambda_payload),
        )
        response_body_raw = json.loads(response.get("Payload").read())["body"]
        get_service_response = json.loads(response_body_raw)
        if get_service_response["status"] == "success":
            groups_data = get_service_response["data"].get("groups", [])
            for group_data in groups_data:
                if group_data["group_id"] == group_id:
                    return group_data["endpoints"][0]["endpoint"]
        raise Exception("Unable to fetch daemon Endpoint information for service %s under organization %s for %s group.",
                        service_id, org_id, group_id)

    def token_for_free_call(self, email, org_id, service_id, group_id,user_public_key):
        signer_public_key_checksum = Web3.toChecksumAddress(SIGNER_ADDRESS)
        current_block_number = self.obj_blockchain_utils.get_current_block_no()
        expiry_date_block = current_block_number + FREE_CALL_EXPIRY
        token_for_free_call = self.obj_blockchain_utils.generate_signature_bytes(["string", "address", "uint256"],
                                                                                 [email, signer_public_key_checksum,
                                                                                  expiry_date_block],
                                                                                 SIGNER_KEY)

        signature = self.obj_blockchain_utils.generate_signature_bytes(
            ["string", "string", "string", "string", "string", "uint256", "bytes32"],
            ["__prefix_free_trial", email, org_id, service_id, group_id,
             current_block_number, token_for_free_call],
            SIGNER_KEY)

        token_with_expiry_for_free_call = ""
        daemon_endpoint = self._get_daemon_endpoint_for_group(org_id, service_id, group_id)
        logger.info(f"Got daemon endpoint {daemon_endpoint} for org {org_id} service {service_id} group {group_id}")

        if self._is_free_call_available(email, token_for_free_call, expiry_date_block, signature,
                                        current_block_number, daemon_endpoint):

            token_with_expiry_for_free_call = self.obj_blockchain_utils.generate_signature_bytes(
                ["string", "address", "uint256"],
                [email, Web3.toChecksumAddress(user_public_key),
                 expiry_date_block],
                SIGNER_KEY)

        return {"token_for_free_call": str(token_with_expiry_for_free_call),
                "token_issue_date_block": expiry_date_block}
