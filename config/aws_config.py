# aws_config.py
import boto3
import os

def get_dynamodb_resource():
    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    aws_region = os.environ.get("AWS_REGION", "ap-south-1")
    profile_name = os.environ.get("AWS_PROFILE")

    if aws_access_key_id and aws_secret_access_key:
        print("Using AWS credentials from environment variables...")
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
    elif profile_name:
        print(f"Using AWS CLI profile: {profile_name}...")
        session = boto3.Session(profile_name=profile_name, region_name=aws_region)
    else:
        print("Using default AWS CLI credentials...")
        session = boto3.Session(region_name=aws_region)

    return session.resource('dynamodb')