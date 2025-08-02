from db_module.dynamo_handler import (
    add_book_to_db, edit_book, delete_book, get_book_details,
    search_books, filter_books, get_user_history,
    generate_user_id, get_user_details, register_user
)

from reading_tracker.tracker import (
    get_all_books_for_user,
    update_book_progress_in_db,
    archive_single_book_in_db,
    unarchive_single_book_in_db
)

from decimal import Decimal, InvalidOperation
import re
from datetime import datetime

def get_validated_rating():
    while True:
        rating_str = input("Rating (1-5): ").strip()
        if not rating_str:
            return None
        try:
            rating_val = Decimal(rating_str)
            if 1 <= rating_val <= 5:
                return rating_val
            else:
                print("‼️  Error: Rating must be between 1 and 5...")
        except InvalidOperation:
            print("‼️  Error: Rating must be a valid number...")

def get_validated_status():
    valid_statuses = ['completed', 'to-read', 'reading']
    while True:
        status = input("Status (Completed/To-read/Reading): ").strip().lower()
        if status in valid_statuses:
            return status
        else:
            print("⚠️  Invalid status!")

def get_validated_field():
    valid_fields = ['title', 'author', 'genre', 'rating', 'tags', 'total_pages']
    while True:
        field = input(f"Field to update ({'/'.join(valid_fields)}): ").strip().lower()
        if field in valid_fields:
            return field
        else:
            print("⚠️  Invalid field!")

def add_book_interface(user_id):   
    while True:
        title = input("Title: ").strip()
        if title: break
        print("‼️  Error: Title cannot be empty...")
    
    while True:
        author = input("Author: ").strip()
        if author: break
        print("‼️  Error: Author cannot be empty...")

    genre = input("Genre (optional): ").strip()
    rating = get_validated_rating()
    status = get_validated_status()  
    tags = input("Tags (e.g., adventure, philosophy): ").strip()
    
    # Get total pages for every new book
    while True:
        try:
            total_pages_str = input("Enter total pages in the book: ").strip()
            if total_pages_str and int(total_pages_str) > 0:
                total_pages = int(total_pages_str)
                break
            print("‼️  Error: Total pages must be a positive number...")
        except ValueError:
            print("‼️  Error: Please enter a valid number...")
            
    # 2. Determine pages_read based on the status
    pages_read = 0
    if status == 'completed':
        pages_read = total_pages
    elif status == 'to-read':
        pages_read = 0
    elif status == 'reading':
        while True:
            try:
                pages_read_str = input(f"Enter number of pages read so far: ").strip()
                pages_val = int(pages_read_str)
                if 0 <= pages_val <= total_pages:
                    pages_read = pages_val
                    break
                print(f"‼️  Error: Pages read must be between 0 and {total_pages}...")
            except ValueError:
                print("‼️  Error: Please enter a valid number...")

    # 3. Add the new progress fields to the data dictionary
    book_data = {
        "title": title, "author": author, "genre": genre,
        "rating": rating, "status": status, "tags": tags,
        "total_pages": total_pages,
        "pages_read": pages_read
    }
    
    add_book_to_db(user_id, book_data)

def get_confirmation(prompt_message):
    confirm = input(f"{prompt_message} (y/n): ").strip().lower()
    if confirm == 'y':
        return True
    elif confirm == 'n':
        return False
    else:
        return None
    
def format_book(book):
    rating_val = book.get('rating')
    rating_display = float(rating_val) if rating_val is not None else "N/A"

    return {
        "book_id": book.get("book_id", "N/A"),
        "user_id": book.get("user_id", "N/A"),
        "title": book.get("title", "N/A"),
        "author": book.get("author", "N/A"),
        "genre": book.get("genre", "N/A"),
        "rating": rating_display,
        "status": book.get("status", "N/A").capitalize(),
        "tags": book.get("tags", []),
        "timestamp": book.get("timestamp", "N/A")
    }

def display_books(books):
    if not books:
        print("⚠️  No books to display!")
        return

    for book in books:
        formatted_book = format_book(book)
        print("-" * 40) 
        for key, value in formatted_book.items():
            print(f"{key.replace('_', ' ').capitalize():<12}: {value}")
    print("-" * 40)

def view_recommendations_interface(user_id):
    print("📚 Personalized Recommendations:")
    user_details = get_user_details(user_id)
    recommendations = user_details.get('recommendations')

    if not recommendations:
        print("‼️  None found...")
        return

    for idx, rec in enumerate(recommendations, 1):
        title = rec.get('title', 'N/A')
        author = rec.get('author', 'N/A')
        print(f"{idx}. \"{title}\" by {author}")

def is_valid_book_id_format(book_id):
    pattern = re.compile(r'^B\d{4}$')
    return bool(pattern.match(book_id))

def is_valid_user_id_format(user_id):
    pattern = re.compile(r'^U\d{4}$')
    return bool(pattern.match(user_id))

def update_progress_interface(user_id):
    book_id = input("Enter the Book ID (e.g., B1001): ").strip().upper()
    if not is_valid_book_id_format(book_id):
        print("⚠️  Invalid Book ID format!")
        return
        
    book = get_book_details(user_id, book_id)
    if not book:
        print("‼️  Book not found...")
        return
    
    print(f"Updating progress for: '{book.get('title')}'...")

    # Get total_pages from the existing book record
    total_pages = book.get('total_pages')
    if not total_pages:
        print("‼️  Error: Total pages not found. Edit the book to add it...")
        return

    # 1. Ask for the new status first
    new_status = get_validated_status()
    
    # 2. Determine pages_read based on the new status
    pages_read = 0
    if new_status == 'completed':
        pages_read = total_pages
        print(f"✅ Status set to 'Completed'!")
    elif new_status == 'to-read':
        pages_read = 0
        print(f"✅ Status set to 'To-read'!")
    elif new_status == 'reading':
        # Only ask for pages if the status is 'reading'
        while True:
            try:
                pages_read_str = input(f"Enter number of pages read so far: ").strip()
                pages_val = int(pages_read_str)
                if 0 <= pages_val <= total_pages:
                    pages_read = pages_val
                    break
                print(f"‼️  Error: Pages read must be between 0 and {total_pages}...")
            except ValueError:
                print("‼️  Error: Please enter a valid number...")
            
    # 3. Ask for the deadline (optional)
    deadline_input = input("Enter deadline (YYYY-MM-DD) (optional): ").strip()
    deadline = book.get('deadline') # Keep old deadline by default
    if deadline_input:
        try:
            datetime.strptime(deadline_input, "%Y-%m-%d")
            deadline = deadline_input
        except ValueError:
            print("⚠️  Invalid date format. Using previous deadline if available!")
            
    progress_data = {
        'total_pages': total_pages,
        'pages_read': pages_read,
        'status': new_status,
        'deadline': deadline
    }
    
    success, percent = update_book_progress_in_db(user_id, book_id, progress_data)
    if success:
        print(f"✅ Progress updated!")

def view_progress_interface(user_id):
    books = get_all_books_for_user(user_id)
    if not books:
        print("📭 No books found to track!")
        return

    print("\n=== 📖 Your Reading Progress ===")
    for book in books:
        if 'progress_percent' in book:
            title = book.get('title', 'N/A')
            pages_read = book.get('pages_read', 0)
            total_pages = book.get('total_pages', 1) # Avoid division by zero
            percent = book.get('progress_percent', 0)
            status = book.get('status', 'N/A')
            print(f"- {title}: {pages_read}/{total_pages} pages ({round(float(percent), 1)}%), Status: {status.capitalize()}")

def view_deadlines_interface(user_id):
    books = get_all_books_for_user(user_id)
    today = datetime.today().date()
    upcoming, overdue = [], []

    for book in books:
        deadline_str = book.get('deadline')
        if not deadline_str: continue
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            if book.get('status') != 'completed':
                (upcoming if deadline >= today else overdue).append((book.get('title'), deadline_str))
        except: continue

    print("\n=== Upcoming Deadlines ===")
    if upcoming:
        for title, d in sorted(upcoming, key=lambda x: x[1]): print(f"• {title}: Due by {d}")
    else: print("📅 No upcoming deadlines!")

    print("\n=== Overdue Books ===")
    if overdue:
        for title, d in sorted(overdue, key=lambda x: x[1]): print(f"• {title}: Was due on {d}")
    else: print("⚠️  No overdue books!")

def archive_book_interface(user_id):
    book_id = input("Enter the Book ID (e.g., B1001): ").strip().upper()
    if not is_valid_book_id_format(book_id):
        print("⚠️  Invalid Book ID format!")
        return
        
    book = get_book_details(user_id, book_id)
    if not book:
        print("‼️  Book not found...")
        return

    # Check if the book is eligible for archiving
    if book.get('status') != 'completed':
        print("❌ This book is not marked as 'Completed' yet!")
        return
        
    if book.get('archived') is True:
        print("📘 This book has already been archived!")
        return

    # If eligible, ask for confirmation
    title = book.get('title', 'N/A')
    confirmation = get_confirmation(f"Are you sure?")
    
    if confirmation is True:
        success = archive_single_book_in_db(user_id, book_id)
        if success:
            print(f"✅ Book '{title}' has been archived!")
    elif confirmation is False:
        print("❌ Operation cancelled!")
    else:
        print("⚠️  Invalid choice!")

def unarchive_book_interface(user_id):
    book_id = input("Enter the Book ID (e.g., B1001): ").strip().upper()
    if not is_valid_book_id_format(book_id):
        print("⚠️  Invalid Book ID format!")
        return
        
    book = get_book_details(user_id, book_id)
    if not book:
        print("‼️  Book not found...")
        return

    # Check if the book is eligible for un-archiving
    if not book.get('archived'):
        print("📘 This book is not currently archived!")
        return

    # If eligible, ask for confirmation
    title = book.get('title', 'N/A')
    confirmation = get_confirmation(f"Are you sure?")
    
    if confirmation is True:
        success = unarchive_single_book_in_db(user_id, book_id)
        if success:
            print(f"✅ Book '{title}' has been un-archived!")
    elif confirmation is False:
        print("❌ Operation cancelled!")
    else:
        print("⚠️  Invalid choice!")

def main():
    try:
        confirmation = get_confirmation("Are you a returning user?")
        
        user_id = None
        if confirmation is True:
            user_id_input = input("Enter your user ID (e.g., U1001): ").strip().upper()

            if not is_valid_user_id_format(user_id_input):
                print("⚠️  Invalid User ID format!")
                return

            user_details = get_user_details(user_id_input)
            if not user_details:
                print("‼️  Error: User ID not found...")
                return 

            user_id = user_id_input
            name = user_details.get("name", "User")
            print(f"👋 Welcome back! Logged in as {name}...")

        elif confirmation is False: 
            name = input("Enter your name: ").strip()
            user_id = generate_user_id()
            register_user(user_id, name)
            print(f"👋 Hello {name}! Your new User ID is: {user_id}")
            
        else: 
            print("⚠️  Invalid choice. Please restart!")
            return

        while True:
            print("\n===== Reading Tracker =====")
            print("1. Add Book", "2. Edit Book", "3. Delete Book", "4. Search Book", "5. Filter Books", "6. View Reading History", "7. View Recommendations", "8. Update Reading Progress", "9. View Progress", "10. View Deadlines", "11. Archive a Book", "12. Unarchive a Book", "13. Exit", sep='\n')
            
            choice = input("Choose an option: ").strip()

            if choice == "1":
                add_book_interface(user_id)

            elif choice == "2":
                book_id = input("Enter Book ID (e.g., B1001): ").strip().upper()

                if not is_valid_book_id_format(book_id):
                    print("⚠️  Invalid Book ID format!")
                    continue

                book = get_book_details(user_id, book_id)
                if not book:
                    print("‼️  Error: Book not found...")
                    continue

                print(f"\nEditing book: '{book.get('title')}'")
                
                field = get_validated_field()
                    
                value = input(f"New value for {field}: ").strip()
                
                # Create the dictionary to hold all fields that will be updated
                updated_fields = {field: value}

                if field == 'rating':
                    try:
                        # We only need to check if it's a valid number here
                        Decimal(value)
                    except InvalidOperation:
                        print("⚠️  Invalid rating! Must be a number. Edit cancelled.")
                        continue
                
                elif field == 'total_pages':
                    try:
                        total_pages_val = int(value)
                        pages_read = book.get('pages_read', 0)

                        if total_pages_val <= 0:
                            print("‼️  Error: Total pages must be a positive number. Edit cancelled.")
                            continue
                        if total_pages_val < pages_read:
                            print(f"‼️  Error: New total pages ({total_pages_val}) cannot be less than pages already read ({pages_read}). Edit cancelled.")
                            continue
                            
                        # Automatically recalculate progress and add it to the update
                        new_percent = round(Decimal(pages_read) / Decimal(total_pages_val) * 100, 2)
                        updated_fields['total_pages'] = total_pages_val # Ensure it's the int value
                        updated_fields['progress_percent'] = new_percent

                    except ValueError:
                        print("‼️  Error: Total pages must be a valid number. Edit cancelled.")
                        continue

                edit_book(user_id, book_id, updated_fields)

            elif choice == "3":
                book_id = input("Enter Book ID (e.g., B1001): ").strip().upper()

                if not is_valid_book_id_format(book_id):
                    print("⚠️  Invalid Book ID format!")
                    continue

                book = get_book_details(user_id, book_id)
                if not book:
                    print("‼️  Book not found...")
                else:
                    title = book.get('title', 'N/A')
                    author = book.get('author', 'N/A')
                    delete_confirmation = get_confirmation(f"Are you sure?")
                    if delete_confirmation is True:
                        delete_book(user_id, book_id)
                    elif delete_confirmation is False:
                        print("❌ Deletion cancelled!")
                    else:
                        print("‼️  Invalid choice. Deletion cancelled...")

            elif choice == "4":
                keyword = input("Enter title or author keyword: ").strip()
                results = search_books(user_id, keyword)
                if results: display_books(results)
                else: print("‼️  No results found...")

            elif choice == "5":
                genre = input("\nGenre (optional): ").strip() or None
                rating = input("Rating (optional): ").strip() or None
                status = input("Status (optional): ").strip().lower() or None
                results = filter_books(user_id, genre, rating, status)
                if results: display_books(results)
                else: print("‼️  No books matched your filters...")

            elif choice == "6":
                history = get_user_history(user_id)
                if history:
                    print("\n=== Your Reading History ===")
                    display_books(history)
                else: print("‼️  No history found...")

            elif choice == "7":
                view_recommendations_interface(user_id)

            elif choice == "8":
                update_progress_interface(user_id)
            elif choice == "9":
                view_progress_interface(user_id)
            elif choice == "10":
                view_deadlines_interface(user_id)
            elif choice == "11":
                archive_book_interface(user_id)
            elif choice == "12":
                unarchive_book_interface(user_id)
            elif choice == "13":
                print("👋 Goodbye!")
                break
            else:
                print("⚠️  Invalid choice!")
                
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user. Goodbye!")

if __name__ == "__main__":
    main()