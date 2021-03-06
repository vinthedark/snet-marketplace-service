import json

import boto3
from botocore.config import Config


class BotoUtils:
    def __init__(self, region_name):
        self.region_name = region_name

    def get_ssm_parameter(self, parameter, config=Config(retries={'max_attempts': 1})):
        """ Format config=Config(connect_timeout=1, read_timeout=0.1, retries={'max_attempts': 1}) """
        ssm = boto3.client('ssm', region_name=self.region_name, config=config)
        parameter = ssm.get_parameter(Name=parameter, WithDecryption=True)
        return parameter["Parameter"]["Value"]

    def invoke_lambda(self, lambda_function_arn, invocation_type, payload, config=Config(retries={'max_attempts': 1})):
        """ Format config=Config(connect_timeout=1, read_timeout=0.1, retries={'max_attempts': 1}) """
        lambda_client = boto3.client('lambda', region_name=self.region_name, config=config)
        lambda_response = lambda_client.invoke(FunctionName=lambda_function_arn, InvocationType=invocation_type,
                                               Payload=payload)
        return json.loads(lambda_response.get('Payload').read())

    def s3_upload_file(self, filename, bucket, key):
        s3_client = boto3.client('s3')
        s3_client.upload_file(filename, bucket, key)

    def s3_download_file(self, bucket, key, filename):
        s3_client = boto3.client('s3')
        s3_client.download_file(bucket, key, filename)
