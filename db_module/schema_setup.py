import sys
import os

# Add parent directory to system path to enable module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import custom AWS DynamoDB resource
from config.aws_config import get_dynamodb_resource
dynamodb = get_dynamodb_resource()

# Create the books table with user_id as partition key and book_id as sort key
def create_books_table():
    try:
        table = dynamodb.create_table(
            TableName='ReadingTrackerBooks',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'book_id', 'KeyType': 'RANGE'}  # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},  # String type
                {'AttributeName': 'book_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand billing
        )
        table.wait_until_exists()  # Wait until table is fully created
        print("✅ ReadingTrackerBooks table created successfully!")
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        # Table already exists
        print("💡 ReadingTrackerBooks table already exists!")

# Create the users table with only user_id as primary key
def create_users_table():
    try:
        table = dynamodb.create_table(
            TableName='ReadingTrackerUsers',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'}  # String type
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand billing
        )
        table.wait_until_exists()
        print("✅ ReadingTrackerUsers table created successfully!")
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        # Table already exists
        print("💡 ReadingTrackerUsers table already exists!")

# Create the counters table to store app-wide counters like book ID generator
def create_counters_table():
    try:
        table = dynamodb.create_table(
            TableName='ReadingTrackerCounters',
            KeySchema=[
                {'AttributeName': 'counter_name', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'counter_name', 'AttributeType': 'S'}  # String type
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand billing
        )
        table.wait_until_exists()
        print("✅ ReadingTrackerCounters table created successfully!")
        
        # Initialize the global book ID counter (e.g., B1001, B1002, etc.)
        table.put_item(Item={
            'counter_name': 'book_id_counter',
            'current_value': 1000  # Starting counter value
        })
        print("▶️  Global book ID counter initialized...")
        
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        # Table already exists
        print("💡 ReadingTrackerCounters table already exists!")

# Execute table creation when this script is run directly
if __name__ == "__main__":
    create_books_table()
    create_users_table()
    create_counters_table()