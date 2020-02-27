import json
import traceback

from common.constant import StatusCode, ResponseStatus
from common.logger import get_logger
from common.repository import Repository
from common.utils import Utils, validate_dict, generate_lambda_response, make_response_body
from wallets.config import NETWORK_ID, NETWORKS, SLACK_HOOK
from wallets.error import Error
from wallets.service.wallet_service import WalletService

NETWORKS_NAME = dict((NETWORKS[netId]['name'], netId) for netId in NETWORKS.keys())
repo = Repository(net_id=NETWORK_ID, NETWORKS=NETWORKS)
utils = Utils()
logger = get_logger(__name__)
wallet_service = WalletService(repo=repo)


def create_channel(event, context):
    logger.info("Received request to initiate order")
    try:
        payload = json.loads(event["body"])
        required_keys = ["order_id", "sender", "signature", "r", "s", "v", "current_block_no",
                         "group_id", "org_id", "amount", "currency", "recipient", "amount_in_cogs"]
        if validate_dict(payload, required_keys):
            logger.info(f"Payload for create channel: {payload}")
            response = wallet_service.open_channel_by_third_party(
                order_id=payload['order_id'], sender=payload['sender'], signature=payload['signature'],
                r=payload['r'], s=payload['s'], v=payload['v'], current_block_no=payload['current_block_no'],
                group_id=payload['group_id'], org_id=payload["org_id"], recipient=payload['recipient'],
                amount=payload['amount'], currency=payload['currency'],
                amount_in_cogs=payload['amount_in_cogs']
            )
            return generate_lambda_response(StatusCode.CREATED, make_response_body(
                ResponseStatus.SUCCESS, response, {}), cors_enabled=False)
        else:
            response = "Bad Request"
            logger.error(f"response: {response}\n"
                         f"event: {event}")
            return generate_lambda_response(StatusCode.BAD_REQUEST, make_response_body(
                ResponseStatus.FAILED, response, {}
            ), cors_enabled=False)
    except Exception as e:
        response = "Failed create channel"
        logger.error(f"response: {response}\n"
                     f"event: {event}\n"
                     f"error: {repr(e)}")
        utils.report_slack(1, str(repr(e)), SLACK_HOOK)
        traceback.print_exc()
        return generate_lambda_response(StatusCode.INTERNAL_SERVER_ERROR, make_response_body(
            ResponseStatus.FAILED, response, Error.undefined_error(repr(e))
        ), cors_enabled=False)


def record_create_channel_event(event, context):
    logger.info("Received request to initiate order")
    try:
        payload = json.loads(event["body"])
        required_keys = ["order_id", "sender", "signature", "r", "s", "v", "current_block_no",
                         "group_id", "org_id", "amount", "currency", "recipient", "amount_in_cogs"]
        if validate_dict(payload, required_keys):
            logger.info(f"Payload for create channel: {payload}")
            response = wallet_service.record_create_channel_event(payload)
            return generate_lambda_response(StatusCode.CREATED, make_response_body(
                ResponseStatus.SUCCESS, response, {}), cors_enabled=False)
        else:
            response = "Bad Request"
            logger.error(f"response: {response}\n"
                         f"event: {event}")
            return generate_lambda_response(StatusCode.BAD_REQUEST, make_response_body(
                ResponseStatus.FAILED, response, {}
            ), cors_enabled=False)
    except Exception as e:
        response = "Failed to record create channel event"
        logger.error(f"response: {response}\n"
                     f"stage: {NETWORK_ID}"
                     f"event: {event}\n"
                     f"error: {repr(e)}")
        utils.report_slack(1, str(repr(e)), SLACK_HOOK)
        traceback.print_exc()
        return generate_lambda_response(StatusCode.INTERNAL_SERVER_ERROR, make_response_body(
            ResponseStatus.FAILED, response, Error.undefined_error(repr(e))
        ), cors_enabled=False)
