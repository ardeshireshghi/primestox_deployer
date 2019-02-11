import boto3


def client():
    return boto3.resource('ec2')
