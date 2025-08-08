import boto3
import os

def get_dynamodb_resource():
    # Read AWS credentials and region from environment variables
    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    aws_region = os.environ.get("AWS_REGION", "ap-south-1")  # Default region if not set
    profile_name = os.environ.get("AWS_PROFILE")

    if aws_access_key_id and aws_secret_access_key:
        print("Using AWS credentials from environment variables...")
        # Create session with explicit access keys
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
    elif profile_name:
        print(f"Using AWS CLI profile: {profile_name}...")
        # Create session using AWS CLI profile
        session = boto3.Session(profile_name=profile_name, region_name=aws_region)
    else:
        print("Using default AWS CLI credentials...")
        # Create session with default AWS CLI configuration
        session = boto3.Session(region_name=aws_region)

    return session.resource('dynamodb')  # Return DynamoDB resource