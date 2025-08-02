# Import boto3 to interact with AWS services.
import boto3
# Import os to access environment variables.
import os

def get_dynamodb_resource():
    """
    Returns a DynamoDB resource using a specific or default AWS profile.
    """
    # Get AWS profile name from environment variable.
    profile_name = os.environ.get('AWS_PROFILE')

    # Check if a profile name was found.
    if profile_name:
        # Print the profile being used.
        print(f"Using AWS Profile: {profile_name}...")
        # Create session with the specified profile.
        session = boto3.Session(profile_name=profile_name)
    else:
        # Use default profile if no profile is set.
        print("Using default AWS profile...")
        # Create session with default credentials.
        session = boto3.Session()

    # Return DynamoDB resource for ap-south-1 region.
    return session.resource('dynamodb', region_name='ap-south-1')