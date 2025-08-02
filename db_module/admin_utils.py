import sys
import os
import boto3
import re
from boto3.dynamodb.conditions import Key

# This block runs first to ensure only an authorized admin can proceed.
try:
    sts_client = boto3.client('sts')
    identity = sts_client.get_caller_identity()
    user_arn = identity.get('Arn')
    print(f"🚀 Running script as IAM User: {user_arn}...")

    # This simple check ensures only users with '-admin' in their name can run the script.
    if '-admin' not in user_arn:
        print("‼️  ACCESS DENIED: This can only be run by an admin...")
        sys.exit(1) # Exit the script immediately

    print("✅ Admin identity confirmed!")

except Exception as e:
    print(f"⚠️  A security error occurred: {e}...")
    print("‼️  Cannot verify permissions. Exiting...")
    sys.exit(1)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.aws_config import get_dynamodb_resource
from db_module.dynamo_handler import generate_user_id, register_user

# --- DynamoDB Setup ---
dynamodb = get_dynamodb_resource()
books_table = dynamodb.Table('ReadingTrackerBooks')
users_table = dynamodb.Table('ReadingTrackerUsers')
counters_table = dynamodb.Table('ReadingTrackerCounters')

def clear_table(table, table_name):    
    response = table.scan()
    items = response.get('Items', [])
    if not items:
        print(f"⚠️  {table_name} is already empty!")
        return
    with table.batch_writer() as batch:
        for item in items:
            key = {k['AttributeName']: item[k['AttributeName']] for k in table.key_schema}
            batch.delete_item(Key=key)
    print(f"▶️  Clearing all items from {table_name}...")
    print(f"✅ All items deleted from {table_name}!")

def show_all_books():
    print("\n=== Books in ReadingTrackerBooks ===")
    try:
        response = books_table.scan()
        books = response.get('Items', [])
        if not books:
            print("‼️  No books found...")
        else:
            sorted_books = sorted(books, key=lambda b: int(b['book_id'][1:]))
            print(f"{'Book ID'.ljust(8)} | {'User ID'.ljust(8)} | {'Status'.ljust(11)} | {'Rating'.ljust(6)} | {'Title'.ljust(40)} | {'Author'}")
            print(f"{'-'*8} | {'-'*8} | {'-'*11} | {'-'*6} | {'-'*40} | {'-'*20}")
            for book in sorted_books:
                book_id, user_id, title, author, status = (book.get(k, 'N/A') for k in ['book_id', 'user_id', 'title', 'author', 'status'])
                rating_display = str(book.get('rating')) if book.get('rating') is not None else "N/A"
                print(f"{book_id.ljust(8)} | {user_id.ljust(8)} | {status.capitalize().ljust(11)} | {rating_display.ljust(6)} | {title.ljust(40)} | {author}")
    except Exception:
        print("‼️  An error occurred while fetching books...")

def show_all_users():
    print("\n=== Users in ReadingTrackerUsers ===")
    try:
        response = users_table.scan()
        users = response.get('Items', [])

        if not users:
            print("‼️  No users found...")
            return
            
        sorted_users = sorted(users, key=lambda u: int(u['user_id'][1:]))
        
        for user in sorted_users:
            user_id = user.get('user_id', 'N/A')
            name = user.get('name', 'N/A')
            joined_date = user.get('timestamp', 'N/A')

            # Print a header for each user for better readability
            print(f"\n--- {name} ({user_id}) | Joined: {joined_date} ---")
            
            # Check for and display the recommendations list
            recommendations = user.get('recommendations')
            if recommendations:
                print("📚 Recommendations:")
                for rec in recommendations:
                    title = rec.get('title', 'N/A')
                    author = rec.get('author', 'N/A')
                    print(f"- \"{title}\" by {author}")
            else:
                print("📚 Recommendations: None found!")
                
    except Exception as e:
        print(f"‼️  An error occurred while fetching users...")

def get_confirmation(prompt_message):
    confirm = input(f"{prompt_message} (y/n): ").strip().lower()
    if confirm == 'y':
        return True
    elif confirm == 'n':
        return False
    else:
        return None
    
def is_valid_user_id_format(user_id):
    return bool(re.match(r'^U\d{4}$', user_id))

def get_existing_user_id():
    while True:
        user_id = input("Enter the User ID (e.g., U1001): ").strip().upper()
        if not is_valid_user_id_format(user_id):
            print("‼️  Error: Invalid User ID format...")
            continue

        response = users_table.get_item(Key={'user_id': user_id})
        if 'Item' in response:
            return user_id, response['Item']
        else:
            print(f"‼️  Error: User not found...")

def delete_specific_user():
    try:
        user_id, user_item = get_existing_user_id()
        print("💡 User found!")
        books_response = books_table.query(KeyConditionExpression=Key("user_id").eq(user_id))
        books_to_delete = books_response.get('Items', [])
        print(f"💡 Found {len(books_to_delete)} associated book(s)!")
        
        confirmation = get_confirmation("Are you sure?")
        if confirmation is True:
            # First, delete all books associated with the user if any exist.
            if books_to_delete:
                with books_table.batch_writer() as batch:
                    for book in books_to_delete:
                        batch.delete_item(Key={'user_id': user_id, 'book_id': book['book_id']})
            
            # After deleting the books, delete the user item itself.
            users_table.delete_item(Key={'user_id': user_id})

            print("✅ User and all associated data deleted successfully!")
        elif confirmation is False:
            print("❌ Deletion cancelled!")
        else:
            print("⚠️  Invalid choice!")
    except Exception as e:
        print(f"‼️  An error occurred...")

def is_valid_book_id_format(book_id):
    return bool(re.match(r'^B\d{4}$', book_id))

def get_existing_book_for_user(user_id):
    while True:
        book_id = input("Enter the Book ID (e.g., B1001): ").strip().upper()
        if not is_valid_book_id_format(book_id):
            print("‼️  Error: Invalid Book ID format...")
            continue

        response = books_table.get_item(Key={'user_id': user_id, 'book_id': book_id})
        if 'Item' in response:
            return book_id, response['Item']
        else:
            print(f"‼️  Error: Book not found...")

def delete_specific_book():
    try:
        user_id, _ = get_existing_user_id()
        book_id, book_item = get_existing_book_for_user(user_id)        
        print("💡 Book found!")
        confirmation = get_confirmation("Are you sure?")
        if confirmation is True:
            books_table.delete_item(Key={'user_id': user_id, 'book_id': book_id})
            print("✅ Book deleted successfully!")
        elif confirmation is False:
            print("❌ Deletion cancelled!")
        else:
            print("⚠️  Invalid choice!")
    except Exception as e:
        print(f"‼️  An error occurred...")

def show_global_counter():
    try:
        response = counters_table.get_item(Key={'counter_name': 'book_id_counter'})
        if 'Item' in response:
            current_value = response['Item']['current_value']
            print(f"Next book ID will be: B{int(current_value) + 1}")
        else:
            print("‼️  Counter not found...")
    except Exception:
        print("‼️  Error fetching counter...")

def _reset_counter_logic():
    try:
        counters_table.put_item(Item={'counter_name': 'book_id_counter', 'current_value': 1000})
        print("✅ Book ID counter has been reset!")
    except Exception as e:
        print(f"‼️ Error resetting counter...")

def reset_book_counter():
    confirmation = get_confirmation("Are you sure?")
    if confirmation is True:
        _reset_counter_logic() # Calls the new internal function
    elif confirmation is False:
        print("❌ Operation cancelled!")
    else:
        print("⚠️ Invalid choice!")

def main():
    try:
        while True:
            print("\n====== ADMIN MENU ======")
            print("1. View ALL Books")
            print("2. View ALL Users")
            print("3. Delete ONLY a Specific Book")
            print("4. Delete ONLY a Specific User")
            print("5. Clear ONLY Books table")
            print("6. Clear ONLY Users table")
            print("7. Clear BOTH tables")
            print("8. View Global Book Counter")
            print("9. Reset Book Counter")
            print("10. Exit")

            choice = input("Enter your choice: ").strip()

            if choice == "1": show_all_books()            
            elif choice == "2": show_all_users()
            elif choice == "3": delete_specific_book()
            elif choice == "4": delete_specific_user()

            elif choice == "5":
                confirmation = get_confirmation("Are you sure?")
                if confirmation is True:
                    clear_table(books_table, "ReadingTrackerBooks")
                elif confirmation is False:
                    print("❌ Operation cancelled!")
                else:
                    print("⚠️  Invalid choice!")()

            elif choice == "6":
                confirmation = get_confirmation("Are you sure?")
                if confirmation is True:
                    clear_table(users_table, "ReadingTrackerUsers")
                elif confirmation is False:
                    print("❌ Operation cancelled!")
                else:
                    print("⚠️  Invalid choice!")

            elif choice == "7":
                confirmation = get_confirmation("Are you sure?")
                if confirmation is True:
                    clear_table(books_table, "ReadingTrackerBooks")
                    clear_table(users_table, "ReadingTrackerUsers")
                    _reset_counter_logic()
                elif confirmation is False:
                    print("❌ Operation cancelled!")
                else:
                    print("⚠️  Invalid choice!")

            elif choice == "8": show_global_counter()
            elif choice == "9": reset_book_counter()
            elif choice == "10":
                print("👋 Goodbye Admin!")
                break
            else:
                print("⚠️  Invalid choice!")
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by admin. Goodbye!")

if __name__ == "__main__":
    main()