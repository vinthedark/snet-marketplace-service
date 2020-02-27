import unittest
import unittest
from unittest.mock import patch, Mock

from event_pubsub.listeners.event_listeners import EventListener, RegistryEventListener


class TestBlockchainEventSubsriber(unittest.TestCase):
    def setUp(self):
        pass

    @patch('event_pubsub.event_repository.EventRepository.read_registry_events')
    @patch('event_pubsub.listeners.listener_handlers.LambdaArnHandler.push_event')
    def test_event_publisher_success(self, mock_push_event,mock_read_registry_event):
        mock_read_registry_event.return_value = [{'row_id': 526, 'block_no': 6247992, 'event': 'ServiceCreated',
          'json_str': "{'orgId': b'snet\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00', 'serviceId': b'freecall\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00', 'metadataURI': b'ipfs://QmQtm73kmKhv6mKTkn7qW3uMPtgK6c5Qytb11sCxY98s5j\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'}",
          'processed': 0,
          'transactionHash': "b'~\\xb5\\x0c\\x93\\xe7y\\xc1\\x9d\\xf2I\\xef3\\xc6H\\x16\\xbd\\xab \\xa4\\xb5\\r\\xaau5eb\\x82B\\xe0\\x1c\\xf7\\xdd'",
          'logIndex': '43', 'error_code': 200, 'error_msg': '', 'row_updated': '2019-10-31 09:44:00',
          'row_created': '2019-10-31 09:44:00'}]
        mock_push_event.return_value={"statusCode":200}

        error_map,succes_list=RegistryEventListener().listen_and_publish_registry_events()
        assert succes_list==[526]



    @patch('event_pubsub.event_repository.EventRepository.read_registry_events')
    @patch('event_pubsub.listeners.listener_handlers.LambdaArnHandler.push_event', side_effect=Exception('Test Error'))
    def test_event_publisher_failure(self, mock_lambda_handler, mock_read_registry_event):
        mock_read_registry_event.return_value = [{'row_id': 526, 'block_no': 6247992, 'event': 'ServiceCreated',
                                                  'json_str': "{'orgId': b'snet\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00', 'serviceId': b'freecall\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00', 'metadataURI': b'ipfs://QmQtm73kmKhv6mKTkn7qW3uMPtgK6c5Qytb11sCxY98s5j\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'}",
                                                  'processed': 0,
                                                  'transactionHash': "b'~\\xb5\\x0c\\x93\\xe7y\\xc1\\x9d\\xf2I\\xef3\\xc6H\\x16\\xbd\\xab \\xa4\\xb5\\r\\xaau5eb\\x82B\\xe0\\x1c\\xf7\\xdd'",
                                                  'logIndex': '43', 'error_code': 200, 'error_msg': '',
                                                  'row_updated': '2019-10-31 09:44:00',
                                                  'row_created': '2019-10-31 09:44:00'}]

        mock_lambda_handler.return_value = {"statusCode": 500}

        error_map, success_list = RegistryEventListener().listen_and_publish_registry_events()
        assert error_map == {526: {'error_code': 500, 'error_message': 'for listener arn:aws got error Test Error'}}