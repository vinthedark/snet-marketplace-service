import os

os.environ["LOG_LEVEL"] = "DEBUG"

NETWORKS = {"db": {
    "HOST": "localhost",
    "USER": "unittest_root",
    "PASSWORD": "unittest_pwd",
    "NAME": "unittest_db",
    "PORT": 3306,
},
}

NETWORK_ID = 0

EVENT_SUBSCRIPTIONS = {"OrganizationCreated": [{"name": "", "type": "lambda_arn",
                                                "url": "arn:aws:lambda:"}],

                       "OrganizationModified": [{"name": "", "type": "lambda_arn",
                                                 "url": "arn:aws:"}],

                       "OrganizationDeleted": [{"name": "", "type": "lambda_arn",
                                                "url": "arn:aws"}],
                       "ServiceCreated": [{"name": "", "type": "lambda_arn",
                                           "url": "arn:aws"}],

                       "ServiceMetadataModified": [{"name": "", "type": "lambda_arn",
                                                    "url": "arn:aws:"}],

                       "ServiceTagsModified": [{"name": "", "type": "lambda_arn",
                                                "url": "arn:aws"}],
                       "ServiceDeleted": [{"name": "", "type": "lambda_arn",
                                           "url": "arn:aws"}],

                       "ChannelOpen": [{"name": "", "type": "lambda_arn",
                                        "url": "arn:aws"}],

                       "ChannelOpen": [{"name": "", "type": "lambda_arn",
                                        "url": "arn:aws"}],
                       "ChannelExtend": [{"name": "", "type": "lambda_arn",
                                          "url": "arn:aws"}],

                       "ChannelAddFunds": [{"name": "", "type": "lambda_arn",
                                            "url": "arn:awser"}],
                       "ChannelSenderClaim": [{"name": "", "type": "lambda_arn",
                                               "url": "arn:aws"}],

                       }

WS_PROVIDER = "wss://ropsten.infura.io/"
REGION_NAME="us-east-2"
SLACK_HOOK = {
    'hostname' : 'https://hooks.slack.com',
    'port': 443,
    'path': '',
    'method': 'POST',
    'headers': {
        'Content-Type': 'application/json'
    }
}
