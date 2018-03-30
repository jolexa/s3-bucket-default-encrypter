#!/usr/bin/env python
import logging
import os
import boto3
from botocore.exceptions import ClientError

logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    s3client = boto3.client('s3')
    buckets = s3client.list_buckets()['Buckets']
    for bucketObj in buckets:
        stop = False
        bucketName = bucketObj['Name']
        print("working on: {}".format(bucketName))
        # Does it have tags?
        try:
            tagsSet = s3client.get_bucket_tagging(Bucket=bucketName)['TagSet']
            for key in tagsSet:
                # Is there an explicit tag to stop callled 'X-StopAutoEncrypt'?
                if key['Key'] == 'X-StopAutoEncrypt':
                    logger.info("Due to tags, excluding bucket '{}'".format(bucketName))
                    stop = True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchTagSet':
                pass # continue onwards, no tags!
        if stop: continue # do not pass go, at this scope
        # Does the bucket already have encryption?
        try:
            encr = s3client.get_bucket_encryption(Bucket=bucketName)
            logger.info("Skipping '{}', already encrypted!")
        except ClientError as e:
            # If not encrypted, then do stuff
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                logger.info("Bucket is not encrypted: '{}' - Enabling default encryption".format(bucketName))
                # Count all the objects
                paginator = s3client.get_paginator('list_objects_v2')
                response_iterator = paginator.paginate(
                    Bucket=bucketName
                )
                for objs in response_iterator:
                    count = objs['KeyCount']
                    # Send a helpful message to the SNS Topic
                    snsclient = boto3.client('sns')
                    snsclient.publish(
                        TopicArn=os.getenv('SNSNotifyArn'),
                        Subject="Attention: Enabled Default Encryption on '{}'".format(bucketName),
                        Message="Bucket '{}' was automatically encrypted, there were {} items that are not encrypted.".format(bucketName, count)
                    )
                    s3client.put_bucket_encryption(
                        Bucket=bucketName,
                        ServerSideEncryptionConfiguration={
                            'Rules': [
                                {
                                    'ApplyServerSideEncryptionByDefault': {
                                        'SSEAlgorithm': 'AES256',
                                    }
                                }
                            ]
                        }
                    )
