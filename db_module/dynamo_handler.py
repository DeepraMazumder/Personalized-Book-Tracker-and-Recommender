import sys
import os

# Add parent directory to system path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from boto3.dynamodb.conditions import Attr, Key
from decimal import Decimal
from botocore.exceptions import ClientError

# Import DynamoDB resource from config
from config.aws_config import get_dynamodb_resource
dynamodb = get_dynamodb_resource()

# Initialize table references
books_table = dynamodb.Table('ReadingTrackerBooks')
users_table = dynamodb.Table('ReadingTrackerUsers')
counters_table = dynamodb.Table('ReadingTrackerCounters')

# Fetch user details from the database
def get_user_details(user_id):
    try:
        response = users_table.get_item(Key={"user_id": user_id})
        return response.get("Item")
    except Exception as e:
        print(f"Error fetching user details...")
        return None

# Register a new user in the users table
def register_user(user_id, name, email):
    try:
        users_table.put_item(
            Item={
                "user_id": user_id,
                "name": name,
                "email": email,
                "recommendations": [],
                "reading_history": [],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "welcome_sent": False
            },
            ConditionExpression='attribute_not_exists(user_id)'  # Prevent overwrite
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f"Error: User ID {user_id} already exists...")
        else:
            print(f"An unexpected AWS error occurred...")
        return False

# Add a new book to the books table
def add_book_to_db(user_id, book_data):
    try:
        title = book_data['title']
        author = book_data['author']

        # Prevent duplicate books
        if is_duplicate(user_id, title, author):
            print("Error: You have already added this book...")
            return False

        book_id = generate_book_id()

        # Calculate reading progress
        total_pages = book_data.get('total_pages', 0)
        pages_read = book_data.get('pages_read', 0)
        progress_percent = 0
        if total_pages > 0:
            progress_percent = round(Decimal(pages_read) / Decimal(total_pages) * 100, 2)

        # Build item to insert into DynamoDB
        item = {
            "user_id": user_id,
            "book_id": book_id,
            "title": title,
            "author": author,
            "genre": book_data['genre'],
            "rating": book_data['rating'],
            "status": book_data['status'],
            "tags": [tag.strip() for tag in book_data['tags'].split(',')] if book_data['tags'] else [],
            "total_pages": total_pages,
            "pages_read": pages_read,
            "progress_percent": progress_percent,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "archived": False
        }

        books_table.put_item(Item=item)
        print(f"Book added successfully! Book ID: {book_id}")
        return True

    except Exception as e:
        print(f"Error adding book to database...")
        raise e

# Fetch specific book details by user_id and book_id
def get_book_details(user_id, book_id):
    try:
        response = books_table.get_item(Key={'user_id': user_id, 'book_id': book_id})
        return response.get("Item")
    except Exception as e:
        print(f"Error fetching book details...")
        return None

# Update existing book information
def edit_book(user_id, book_id, updated_fields):
    try:
        update_expr_parts = []
        expr_values = {}
        expr_names = {}

        # Build the update expression dynamically
        for k, v in updated_fields.items():
            placeholder = f"#attr_{k}"
            update_expr_parts.append(f"{placeholder} = :{k}")
            expr_names[placeholder] = k

            # Handle data type conversions
            if k == "rating":
                expr_values[f":{k}"] = Decimal(v)
            elif k == "tags":
                expr_values[f":{k}"] = [tag.strip() for tag in v.split(',')] if v else []
            else:
                expr_values[f":{k}"] = v

        update_expr = "SET " + ", ".join(update_expr_parts)

        # Perform the update operation
        books_table.update_item(
            Key={"user_id": user_id, "book_id": book_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names
        )
        print("Book updated successfully!")

    except Exception as e:
        print(f"Update failed...")

# Delete a book from the books table
def delete_book(user_id, book_id):
    try:
        response = books_table.get_item(Key={"user_id": user_id, "book_id": book_id})
        if "Item" not in response:
            print("No such book to delete...")
            return

        books_table.delete_item(Key={"user_id": user_id, "book_id": book_id})
        print("Book deleted successfully!")
    except Exception as e:
        print(f"Delete failed...")

# Check for duplicate books based on title and author
def is_duplicate(user_id, title, author):
    response = books_table.query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        FilterExpression=Attr("title").eq(title) & Attr("author").eq(author)
    )
    return len(response['Items']) > 0

# Get a user's reading history (excluding archived books)
def get_user_history(user_id):
    try:
        response = books_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id),
            FilterExpression=Attr('archived').ne(True) | Attr('archived').not_exists()
        )
        return sorted(response.get('Items', []), key=lambda x: x.get('timestamp', ''), reverse=True)
    except Exception as e:
        print(f"Fetching history failed...")
        return []

# Search user's books by title or author keyword
def search_books(user_id, keyword):
    try:
        response = books_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id),
            FilterExpression=Attr("title").contains(keyword) | Attr("author").contains(keyword)
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Search failed...")
        return []

# Filter user's books based on genre, rating, or status
def filter_books(user_id, genre=None, rating=None, status=None):
    try:
        key_condition_expression = Key("user_id").eq(user_id)
        filter_expression = None

        # Dynamically build filter expression
        if genre:
            filter_expression = Attr("genre").eq(genre)
        if rating:
            rating_expr = Attr("rating").eq(Decimal(rating))
            filter_expression = filter_expression & rating_expr if filter_expression else rating_expr
        if status:
            status_expr = Attr("status").eq(status)
            filter_expression = filter_expression & status_expr if filter_expression else status_expr

        query_args = {'KeyConditionExpression': key_condition_expression}
        if filter_expression:
            query_args['FilterExpression'] = filter_expression

        response = books_table.query(**query_args)
        return response.get('Items', [])
    except Exception as e:
        print(f"Filtering failed...")
        return []

# Generate a new user ID by incrementing the highest existing one
def generate_user_id():
    response = users_table.scan(ProjectionExpression="user_id")
    user_ids = [item['user_id'] for item in response['Items'] if item['user_id'].startswith("U")]
    new_id = max([int(uid[1:]) for uid in user_ids], default=1000) + 1
    return f"U{new_id}"

# Generate a new book ID using a counter in the counters table
def generate_book_id():
    try:
        response = counters_table.update_item(
            Key={'counter_name': 'book_id_counter'},
            UpdateExpression='ADD current_value :inc',
            ExpressionAttributeValues={':inc': 1},
            ReturnValues='UPDATED_NEW'
        )
        new_id = int(response['Attributes']['current_value'])
        return f"B{new_id}"

    # Handle missing counter gracefully
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException' or 'does not exist' in str(e):
            try:
                counters_table.put_item(
                    Item={
                        'counter_name': 'book_id_counter',
                        'current_value': 1001
                    },
                    ConditionExpression='attribute_not_exists(counter_name)'
                )
                return "B1001"
            except ClientError:
                return generate_book_id()
        else:
            raise e
    except Exception as e:
        print(f"Error generating book ID...")
        try:
            response = books_table.scan(ProjectionExpression="book_id")
            book_ids = [int(item['book_id'][1:]) for item in response['Items'] if item['book_id'].startswith('B')]
            new_id = max(book_ids, default=1000) + 1
            return f"B{new_id}"
        except:
            return f"B{int(datetime.now().timestamp())}"