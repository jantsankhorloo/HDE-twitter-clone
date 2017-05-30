import boto3
import base64
import config

s3 = boto3.resource(
    service_name='s3',
    endpoint_url='http://127.0.0.1:4567', 
    region_name='',
    aws_access_key_id="",
    aws_secret_access_key="")

s3.create_bucket(Bucket=config.BUCKET_NAME)

def s3_upload(file, data):
    s3.Bucket(config.BUCKET_NAME).put_object(Key=file, Body=data)

def s3_retrieve(file):
    data = s3.Object(config.BUCKET_NAME, file).get()
    return base64.encodestring(data['Body'].read())
