import sys
import os
from datetime import datetime
from decimal import Decimal

# Add parent directory to system path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import custom AWS DynamoDB config and query condition utility
from config.aws_config import get_dynamodb_resource
from boto3.dynamodb.conditions import Key

# Get the DynamoDB resource and reference the books table
dynamodb = get_dynamodb_resource()
books_table = dynamodb.Table('ReadingTrackerBooks')

# Fetch all books associated with a specific user
def get_all_books_for_user(user_id):
    try:
        # Query books by user_id
        response = books_table.query(KeyConditionExpression=Key("user_id").eq(user_id))
        return response.get('Items', [])
    except Exception as e:
        print(f"Error fetching books...")
        return []

# Update reading progress for a specific book in the database
def update_book_progress_in_db(user_id, book_id, progress_data):
    try:
        # Extract total pages and pages read from input
        total_pages = progress_data['total_pages']
        pages_read = progress_data['pages_read']
        # Calculate progress percentage
        progress_percent = round(Decimal(pages_read) / Decimal(total_pages) * Decimal(100), 2)

        # Build list of update expressions
        update_expression_parts = [
            "pages_read = :pr",
            "total_pages = :tp",
            "progress_percent = :pp",
            "#s = :st"  # Use expression alias for reserved word 'status'
        ]

        # Define values for the placeholders
        expression_values = {
            ':pr': pages_read,
            ':tp': total_pages,
            ':pp': progress_percent,
            ':st': progress_data['status']
        }

        # Define name substitution for reserved keyword
        expression_names = {'#s': 'status'}

        # Optionally add deadline if present
        if progress_data.get('deadline'):
            update_expression_parts.append("deadline = :d")
            expression_values[':d'] = progress_data['deadline']
        
        # Optionally add rating if provided
        if 'rating' in progress_data:
            update_expression_parts.append("rating = :r")
            expression_values[':r'] = progress_data['rating']

        # Perform the update operation
        books_table.update_item(
            Key={'user_id': user_id, 'book_id': book_id},
            UpdateExpression="SET " + ", ".join(update_expression_parts),
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names
        )

        return True, progress_percent

    except Exception:
        print(f"Error updating progress...")
        return False, 0

# Mark a book as archived in the database
def archive_single_book_in_db(user_id, book_id):
    try:
        books_table.update_item(
            Key={'user_id': user_id, 'book_id': book_id},
            UpdateExpression="SET archived = :a",
            ExpressionAttributeValues={':a': True}
        )
        return True
    except Exception:
        print(f"Error archiving book...")
        return False

# Mark a book as unarchived in the database
def unarchive_single_book_in_db(user_id, book_id):
    try:
        books_table.update_item(
            Key={'user_id': user_id, 'book_id': book_id},
            UpdateExpression="SET archived = :a",
            ExpressionAttributeValues={':a': False}
        )
        return True
    except Exception:
        print(f"Error un-archiving book...")
        return False