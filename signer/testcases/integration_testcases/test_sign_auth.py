import unittest

from eth_account.messages import defunct_hash_message
from web3.auto import w3
import web3

from signer.signature_authenticator import main


class TestSignAuth(unittest.TestCase):

    def test_generate_sign(self):
        username = 'test-user'
        org_id = 'snet'
        group_id = 'cOyJHJdvvig73r+o8pijgMDcXOX+bt8LkvIeQbufP7g='
        service_id = 'example-service'
        block_number = 1234
        signature = 'h9Ssz1bi+aT4NKERkGqJOfx2E9/4Y9czj+YNr4XzXDcnlay37v9Jfown278MFF+VrKsz1r1Ip/CeppwtjhiBtAA='
        headers = {
            'x-username': username,
            'x-organizationid': org_id,
            'x-groupid': group_id,
            'x-serviceid': service_id,
            'x-currentblocknumber': block_number,
            'x-signature': signature
        }
        event = dict()
        event['headers'] = headers
        event['methodArn'] = 'abc'
        response = main(event, None)
        # assert response['policyDocument']['Statement'][0]['Effect'] == 'Allow'


if __name__ == '__main__':
    unittest.main()
