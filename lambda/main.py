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
        bucketName = bucketObj['Name']
        logger.info("working on: {}".format(bucketName))
        # Does the bucket already have encryption?
        try:
            s3client.get_bucket_encryption(Bucket=bucketName)
            logger.info("Skipping '{}', already encrypted!".format(bucketName))
            continue
        except ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                logger.info("Bucket is not encrypted: '{}' - Enabling default encryption".format(bucketName))
            else:
                print(e)
                continue
        # Does it have tags?
        try:
            tagsSet = s3client.get_bucket_tagging(Bucket=bucketName)['TagSet']
            for key in tagsSet:
                # Is there an explicit tag to stop callled 'X-StopAutoEncrypt'?
                if key['Key'] == 'X-StopAutoEncrypt':
                    logger.info("Due to tags, excluding bucket '{}'".format(bucketName))
                    continue
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchTagSet':
                pass # continue onwards, no tags!
            else:
                print(e)
                continue
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
        # Rough count all the objects (don't paginate on purpose)
        r = s3client.list_objects_v2(Bucket=bucketName)
        if r['IsTruncated']:
            count = "1000+"
        else:
            count = r['KeyCount']
        # Send a helpful message to the SNS Topic
        snsclient = boto3.client('sns')
        subj = "(!!): Enabled Encryption on '{}'".format(bucketName)
        snsclient.publish(
            TopicArn=os.getenv('SNSNotifyArn'),
            # 100 char limit
            Subject=(subj[:98] + '..') if len(subj) > 100 else subj,
            Message="Bucket '{}' was automatically encrypted, there were {} items that are [maybe] not encrypted.".format(bucketName, count)
        )
