import streamlit as st
from datetime import datetime, date
import re
from decimal import Decimal, InvalidOperation
import html

# Import custom modules for database handling and tracker logic
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
from dashboard.dashboard_cli import show_dashboard
from dashboard.report_generator import generate_pdf_summary

# Configure the Streamlit page settings
st.set_page_config(
    page_title="SmartReads",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS for a loading animation
st.markdown("""
    <style>
        @keyframes pulse {
            0% { opacity: 0.3; }
            50% { opacity: 1; }
            100% { opacity: 0.3; }
        }
        .loading-text {
            text-align: center;
            font-size: 1.5rem;
            font-weight: bold;
            color: #4A90E2;
            animation: pulse 1.5s infinite;
        }
    </style>
""", unsafe_allow_html=True)

# Utility function to validate the Book ID format (e.g., B1234)
def is_valid_book_id_format(book_id):
    pattern = re.compile(r'^B\d{4}$')
    return bool(pattern.match(book_id))

# Utility function to validate the User ID format (e.g., U1234)
def is_valid_user_id_format(user_id):
    pattern = re.compile(r'^U\d{4}$')
    return bool(pattern.match(user_id))

# Formats book data for clean display in the UI
def format_book_for_display(book):
    rating_val = book.get('rating')
    rating_display = float(rating_val) if rating_val is not None else "N/A"
    
    return {
        "Book ID": book.get("book_id", "N/A"),
        "Title": book.get("title", "N/A"),
        "Author": book.get("author", "N/A"),
        "Genre": book.get("genre", "N/A"),
        "Rating": rating_display,
        "Status": book.get("status", "N/A").capitalize(),
        "Tags": book.get("tags", ""),
        "Total Pages": book.get("total_pages", "N/A"),
        "Pages Read": book.get("pages_read", "N/A"),
        "Progress": f"{book.get('progress_percent', 0)}%" if book.get('progress_percent') else "N/A",
        "Archived": "Yes" if book.get('archived') else "No"
    }

# Initialize session state variables for user session management
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Displays the login and registration page
def show_login():
    # Render the sidebar with information about the application
    with st.sidebar:        
        st.header("💡 About Us")
        st.write(
            "We’re a team of tech enthusiasts building intelligent solutions to help users track reading habits and discover personalized book recommendations using Python and AWS!"
        )
        st.divider()
        
        st.header("🚀 What We Do")
        st.write(
            "We deliver a smart, cloud-powered platform that lets users log books, track reading progress and receive personalized recommendations - making reading organized, engaging and effortlessly managed!"
        )
        
        # Add a footer to the bottom of the sidebar
        st.markdown(
            """
            <style>
                .sidebar-footer {
                    position: fixed;
                    bottom: 20px;
                    left: 20px;
                    width: 270px;
                    font-size: 1rem;
                    font-style: italic;
                    color: #888;
                    text-align: center
                }
            </style>
            <div class="sidebar-footer">
                Developed in July 2025
            </div>
            """,
            unsafe_allow_html=True
        )

    # Render the main page content with login/registration forms
    st.markdown("<h1 style='text-align: center;'>📚 Welcome to SmartReads!</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([0.5, 0.5])
        
    # Column for existing user login
    with col1:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🔄 Returning User")
        user_id_input = st.text_input("Enter your User ID (e.g. U1001):", key="login_user_id")
        # Email input for login
        email_login_input = st.text_input("Enter your email:", key="login_email")
        
        # Center the login button
        _, login_button_col, _ = st.columns([1, 1, 1])
        with login_button_col:
            login_clicked = st.button("Login", key="login_btn", use_container_width=True)

        # Handle the login logic when the button is clicked
        if login_clicked:
            # Check for both User ID and Email
            if user_id_input and email_login_input:
                user_id_upper = user_id_input.strip().upper()
                email_login = email_login_input.strip()

                if is_valid_user_id_format(user_id_upper):
                    user_details = get_user_details(user_id_upper)
                    
                    # Validate email from DB against input
                    if user_details and user_details.get('email') == email_login:
                        # If credentials are correct, log the user in
                        st.session_state.user_id = user_id_upper
                        st.session_state.user_name = user_details.get("name", "User")
                        st.session_state.logged_in = True
                        st.session_state.show_loading_screen = True
                        st.rerun()
                    else:
                        st.error("Invalid User ID or Email!")
                else:
                    st.error("Invalid User ID format!")
            else:
                st.error("Please enter both your User ID and Email!")
    
    # Column for new user registration
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("✨ New User")
        name_input = st.text_input("Enter your name:", key="register_name")
        email_input = st.text_input("Enter your email:", key="register_email")
        st.markdown("<br>", unsafe_allow_html=True)

        # Center the create account button
        _, create_account_button_col, _ = st.columns([1, 1, 1])
        with create_account_button_col:
            create_account_clicked = st.button("Create Account", key="register_btn", use_container_width=True)

        # Handle the registration logic when the button is clicked
        if create_account_clicked:
            name = name_input.strip()
            email = email_input.strip()

            if name and email:
                if "@" in email and "." in email: # Basic email validation
                    user_id = generate_user_id()
                    register_user(user_id, name, email)

                    st.success("Account created! Check your email for a welcome message with your User ID.")
                    st.info("Please confirm the subscription in the first email from AWS to receive future notifications.")

                    # Automatically log the new user in
                    st.session_state.user_id = user_id
                    st.session_state.user_name = name
                    st.session_state.logged_in = True
                    st.session_state.show_loading_screen = True
                    st.rerun()
                else:
                    st.error("Please enter a valid email address!")
            else:
                st.error("Please enter both your name and email!")  

# Main application function, shown after successful login
def main_app():
    # Render the sidebar for navigation
    with st.sidebar:
        st.title(f"👋 Hello, {st.session_state.user_name}!")
        st.write(f"**User ID:** {st.session_state.user_id}")

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.show_logout_screen = True
            st.rerun()

        st.divider()
        st.markdown("### 📍 Navigate to:")

        # Define navigation options
        nav_options = [
            ("📊 Dashboard", "dashboard"), ("➕ Add Book", "add"), ("✏️ Edit Book", "edit"),
            ("🗑️ Delete Book", "delete"), ("🔍 Search Books", "search"), ("🔎 Filter Books", "filter"),
            ("📖 Reading History", "history"), ("💡 Recommendations", "recommend"),
            ("📈 Update Progress", "progress"), ("⏰ View Deadlines", "deadlines"), ("📦 Archive Book", "archive")
        ]

        # Initialize the selected page to dashboard
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = "dashboard"

        # Create full-width navigation buttons
        for label, value in nav_options:
            if st.button(label, use_container_width=True):
                st.session_state.selected_page = value
                st.rerun()

    # Render the selected page based on user navigation
    page = st.session_state.selected_page
    if page == "dashboard":
        show_dashboard()
    elif page == "add":
        show_add_book()
    elif page == "edit":
        show_edit_book()
    elif page == "delete":
        show_delete_book()
    elif page == "search":
        show_search_books()
    elif page == "filter":
        show_filter_books()
    elif page == "history":
        show_reading_history()
    elif page == "recommend":
        show_recommendations()
    elif page == "progress":
        show_update_progress()
    elif page == "deadlines":
        show_view_deadlines()
    elif page == "archive":
        show_archive_book()

# Page for adding a new book
def show_add_book():
    st.title("➕ Add New Book")

    # Initialize session state for the add book form fields
    if "add_title" not in st.session_state:
        st.session_state.add_title = ""
    if "add_author" not in st.session_state:
        st.session_state.add_author = ""
    if "add_genre" not in st.session_state:
        st.session_state.add_genre = ""
    if "add_rating" not in st.session_state:
        st.session_state.add_rating = None
    if "add_status" not in st.session_state:
        st.session_state.add_status = "To-read"
    if "add_tags" not in st.session_state:
        st.session_state.add_tags = ""
    if "add_total_pages" not in st.session_state:
        st.session_state.add_total_pages = 1
    if "add_pages_read" not in st.session_state:
        st.session_state.add_pages_read = 0

    # Callback to handle the logic of adding a book
    def _handle_add_book():
        title = st.session_state.add_title.strip()
        author = st.session_state.add_author.strip()
        total_pages = st.session_state.add_total_pages
        pages_read = st.session_state.add_pages_read

        # Perform validation checks
        if not title or not author:
            st.error("Title and Author are required fields!")
            return
        if total_pages is None or str(total_pages).strip() == "" or int(total_pages) <= 0:
            st.error("Total Pages must be greater than or equal to 1!")
            return
        if pages_read > total_pages:
            st.error("Pages read cannot be greater than total pages!")
            return

        # Prepare book data for database entry
        book_data = {
            "title": title, "author": author,
            "genre": st.session_state.add_genre.strip() if st.session_state.add_genre else None,
            "rating": Decimal(str(st.session_state.add_rating)) if st.session_state.add_rating else None,
            "status": st.session_state.add_status.lower(), "tags": st.session_state.add_tags.strip(),
            "total_pages": int(total_pages), "pages_read": int(pages_read)
        }

        # Attempt to add the book to the database
        try:
            success = add_book_to_db(st.session_state.user_id, book_data)
            if success:
                st.success("Book added successfully!")
                _handle_cancel_add() # Clear form on success
            else:
                st.error("This book already exists in your reading list!")
        except Exception:
            st.error("An unexpected error occurred...")

    # Callback to clear the add book form fields
    def _handle_cancel_add():
        st.session_state.add_title = ""
        st.session_state.add_author = ""
        st.session_state.add_genre = ""
        st.session_state.add_rating = None
        st.session_state.add_status = "To-read"
        st.session_state.add_tags = ""
        st.session_state.add_total_pages = 1
        st.session_state.add_pages_read = 0

    # UI layout for the add book form
    st.markdown("""
        <style> .stButton>button { display: block; margin: 0 auto; } </style>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Title *", key="add_title")
        st.text_input("Author *", key="add_author")
        st.text_input("Genre", key="add_genre")
        st.selectbox("Rating", [None, 1, 2, 3, 4, 5],
                     format_func=lambda x: "Select rating" if x is None else f"{x} ⭐",
                     key="add_rating")
    with col2:
        st.selectbox("Status *", ["To-read", "Reading", "Completed"], key="add_status")
        st.text_input("Tags", key="add_tags")
        st.number_input("Total Pages *", key="add_total_pages", step=1, format="%d")
        st.number_input("Pages Read", min_value=0, key="add_pages_read", step=1, format="%d")

    # Real-time validation for pages read
    pages_read_invalid = st.session_state.add_pages_read > st.session_state.add_total_pages
    if pages_read_invalid:
        st.warning("Pages read cannot be greater than total pages!")

    # Action buttons for the form
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.button("✅ Add", on_click=_handle_add_book, type="primary", disabled=pages_read_invalid)
    with btn_col2:
        st.button("❌ Cancel", on_click=_handle_cancel_add)

# Page for editing an existing book
def show_edit_book():
    st.title("✏️ Edit Book")
    st.markdown("<br>", unsafe_allow_html=True)

    # Initialize session state for edit functionality
    if 'edit_book_input' not in st.session_state:
        st.session_state.edit_book_input = ""

    # Automatically fetch book details if an ID is present in the session state
    if st.session_state.edit_book_input and 'edit_book' not in st.session_state:
        book_id = st.session_state.edit_book_input.strip().upper()
        if is_valid_book_id_format(book_id):
            book = get_book_details(st.session_state.user_id, book_id)
            if book:
                st.session_state.edit_book = book
                st.session_state.edit_book_id = book_id

    # Callback to reset the input widget when the field to edit changes
    def _on_field_change():
        if 'edit_new_value_input' in st.session_state:
            del st.session_state['edit_new_value_input']

    # Callback to find a book based on the provided Book ID
    def _handle_find_book():
        st.session_state.pop("edit_book", None)
        st.session_state.pop("edit_book_id", None)
        _on_field_change()

        book_id = st.session_state.edit_book_input.strip().upper()
        if not book_id:
            st.warning("Please enter a Book ID!")
            return
        if not is_valid_book_id_format(book_id):
            st.error("Invalid Book ID format!")
            st.session_state.edit_book_input = ""
        else:
            book = get_book_details(st.session_state.user_id, book_id)
            if not book:
                st.error("Book not found!")
                st.session_state.edit_book_input = ""
            else:
                st.session_state.edit_book = book
                st.session_state.edit_book_id = book_id

    # Callback to handle the book update logic
    def _handle_update_book():
        field = st.session_state.edit_field_select
        new_value = st.session_state.edit_new_value_input
        book = st.session_state.edit_book
        final_value = new_value
        updated_fields = {}

        # Sanitize text input
        if field in ["title", "author", "genre", "tags"] and isinstance(new_value, str) and not new_value.strip():
            final_value = None

        # Validate required fields
        if field in ["title", "author"] and final_value is None:
            st.error(f"{field.capitalize()} is a required field!")
            return

        # Process the new value and prepare the update payload
        try:
            if field == "total_pages":
                if final_value is None:
                    st.error("Total Pages must be a number greater than or equal to 1!")
                    return
                total_pages_val = int(final_value)
                if total_pages_val <= 0:
                    st.error("Total Pages must be greater than or equal to 1!")
                    return
                pages_read = book.get('pages_read', 0)
                if total_pages_val < pages_read:
                    st.error(f"New total pages ({total_pages_val}) cannot be less than pages read ({pages_read})!")
                    return
                # Recalculate progress percentage
                new_percent = round(Decimal(pages_read) / Decimal(total_pages_val) * 100, 2)
                updated_fields = {'total_pages': total_pages_val, 'progress_percent': new_percent}
            else:
                updated_fields = {field: final_value}
        except (ValueError, TypeError, InvalidOperation):
            st.error(f"Invalid value provided for {field}. Please check your input.")
            return

        # Call the database handler to apply the changes
        try:
            edit_book(st.session_state.user_id, st.session_state.edit_book_id, updated_fields)
            st.success("Book edited successfully!")
            st.session_state.pop("edit_book", None)
            st.session_state.pop("edit_book_id", None)
            st.session_state.edit_book_input = ""
        except Exception as e:
            st.error(f"Update failed. Database error: {e}")
            return

    # Callback to cancel the edit operation and clear the form
    def _handle_cancel_edit():
        st.session_state.pop("edit_book", None)
        st.session_state.pop("edit_book_id", None)
        st.session_state.edit_book_input = ""

    # UI for finding a book to edit
    st.text_input("Book ID", placeholder="e.g. B1001", key="edit_book_input")
    st.button("🔍 Find Book", on_click=_handle_find_book)

    # If a book is found, display the editing form
    if 'edit_book' in st.session_state:
        book = st.session_state.edit_book
        st.success(f"Editing: {book.get('title')} by {book.get('author')}")

        field_options = {
            "title": "Title", "author": "Author", "genre": "Genre",
            "tags": "Tags", "total_pages": "Total Pages"
        }
        field = st.selectbox(
            "Field to Edit", options=[None] + list(field_options.keys()),
            format_func=lambda key: "Choose an option" if key is None else field_options[key],
            key="edit_field_select", on_change=_on_field_change
        )
        
        # Display the correct input widget based on the selected field
        if field:
            current_value = book.get(field, "")
            if field == "total_pages":
                st.number_input("New Total Pages", placeholder=f"Current: {current_value or 'Not Set'}",
                                key="edit_new_value_input", step=1, format="%d")
            else:
                st.text_input(f"New {field_options[field]}", placeholder=f"Current: {current_value or 'Not Set'}",
                              key="edit_new_value_input")

            # Action buttons for editing
            _, col2, _, col4, _ = st.columns(5)
            with col2:
                st.button("💾 Edit", on_click=_handle_update_book, type="primary", use_container_width=True)
            with col4:
                st.button("❌ Cancel", on_click=_handle_cancel_edit, use_container_width=True)

# Page for deleting a book
def show_delete_book():
    st.title("🗑️ Delete Book")
    st.markdown("<br>", unsafe_allow_html=True)

    # Initialize session state for delete functionality
    if 'delete_book_input' not in st.session_state:
        st.session_state.delete_book_input = ""

    # Auto-load book details if an ID is passed to the session
    if st.session_state.delete_book_input and 'delete_book' not in st.session_state:
        book_id = st.session_state.delete_book_input.strip().upper()
        if is_valid_book_id_format(book_id):
            book = get_book_details(st.session_state.user_id, book_id)
            if book:
                st.session_state.delete_book = book
                st.session_state.delete_book_id = book_id

    # Callback to find a book to delete
    def _handle_find_book():
        if 'delete_book' in st.session_state:
            del st.session_state.delete_book
        if 'delete_book_id' in st.session_state:
            del st.session_state.delete_book_id
        
        book_id = st.session_state.delete_book_id_input.strip().upper()
        if not book_id:
            st.warning("Please enter a Book ID!")
            return
        if not is_valid_book_id_format(book_id):
            st.error("Invalid Book ID format!")
            st.session_state.delete_book_id_input = ""
        else:
            book = get_book_details(st.session_state.user_id, book_id)
            if not book:
                st.error("Book not found!")
                st.session_state.delete_book_id_input = ""
            else:
                st.session_state.delete_book = book
                st.session_state.delete_book_id = book_id
    
    # Callback to confirm and execute the deletion
    def _handle_book_delete():
        try:
            delete_book(st.session_state.user_id, st.session_state.delete_book_id)
            st.success("Book deleted successfully!")
            del st.session_state.delete_book
            del st.session_state.delete_book_id
            st.session_state.delete_book_id_input = ""
        except Exception:
            st.error(f"Error deleting book...")

    # Callback to cancel the deletion and clear the form
    def _handle_cancel_delete():
        if 'delete_book' in st.session_state:
            del st.session_state.delete_book
        if 'delete_book_id' in st.session_state:
            del st.session_state.delete_book_id
        st.session_state.delete_book_id_input = ""
        st.session_state.delete_book_input = ""

    # UI for finding a book to delete
    st.text_input("Book ID", placeholder="e.g. B1001", key="delete_book_id_input")
    st.button("🔍 Find Book", on_click=_handle_find_book)

    # If a book is found, show confirmation buttons
    if 'delete_book' in st.session_state:
        book = st.session_state.delete_book
        st.warning(f"Deleting: {book.get('title')} by {book.get('author')}")

        _, col2, _, col4, _ = st.columns(5)
        with col2:
            st.button("🗑️ Delete", type="primary", on_click=_handle_book_delete, use_container_width=True)
        with col4:
            st.button("❌ Cancel", on_click=_handle_cancel_delete, use_container_width=True)

# Page for searching books by title or author
def show_search_books():
    st.title("🔍 Search Books")
    st.markdown("<br>", unsafe_allow_html=True)
    keyword = st.text_input("Search by title or author", placeholder="Enter keyword (case-sensitive)")
    
    if st.button("🔍 Search"):
        results = search_books(st.session_state.user_id, keyword)
        if results:
            st.success(f"Found {len(results)} book(s)...")
            display_books_table(results)
        else:
            st.info("No books found!")

# Page for filtering books by genre, rating, or status
def show_filter_books():
    st.title("🔎 Filter Books")
    st.markdown("<br>", unsafe_allow_html=True) 
    col1, col2, col3 = st.columns(3)
    
    with col1:
        genre = st.text_input("Genre", placeholder="e.g. Fiction")
    with col2:
        rating = st.selectbox("Rating", [None, 1, 2, 3, 4, 5], 
                             format_func=lambda x: "Any rating" if x is None else f"{x} ⭐")
    with col3:
        status = st.selectbox("Status", [None, "To-read", "Reading", "Completed"],
                             format_func=lambda x: "Any status" if x is None else x.capitalize())
    
    if st.button("🔎 Apply"):
        results = filter_books(st.session_state.user_id,
                               genre.strip() if genre.strip() else None,
                               str(rating) if rating else None,
                               status.lower() if status else None)
        if results:
            st.success(f"Found {len(results)} book(s)...")
            display_books_table(results)
        else:
            st.info("No books match your filters!")

# Page to display the user's complete reading history
def show_reading_history():
    st.title("📖 Reading History")
    st.markdown("<br>", unsafe_allow_html=True)
    history = get_user_history(st.session_state.user_id)

    if history:
        history_sorted = sorted(history, key=lambda b: b.get("book_id", ""))
        st.success(f"Showing {len(history_sorted)} book(s) from your history...")
        display_books_table_edit(history_sorted)
    else:
        st.info("No reading history found!")

# Page to display personalized book recommendations
def show_recommendations():
    st.title("💡 Personalized Recommendations")
    st.markdown("<br>", unsafe_allow_html=True)

    # CSS for styling the recommendation cards
    card_css = """
    <style>
        .book-card {
            background-color: #262730; border: 1px solid #3c3d44; border-radius: 8px;
            padding: 20px; margin: 15px 0; height: 200px; display: flex;
            flex-direction: column; justify-content: space-between;
            transition: border-color 0.3s; overflow: hidden;
        }
        .book-card:hover { border-color: #4A90E2; }
        .book-card h4 {
            font-size: 1.1rem; font-weight: 600; color: #FAFAFA; margin: 0 0 10px 0;
            display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
            overflow: hidden; text-overflow: ellipsis; word-wrap: break-word;
        }
        .book-card .author {
            font-style: italic; font-size: 0.95rem; color: #A0A0A5; margin: 0;
            overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
        }
        .book-card .rating {
            font-size: 0.9rem; color: #FFC107; font-weight: 500; margin-top: 10px;
        }
    </style>
    """
    st.markdown(card_css, unsafe_allow_html=True)

    # Fetch and display recommendations
    user_details = get_user_details(st.session_state.user_id)
    recommendations = user_details.get('recommendations', [])

    if recommendations:
        st.success(f"Based on your reading history, here are {len(recommendations)} recommendations...")
        num_columns = 3
        for i in range(0, len(recommendations), num_columns):
            cols = st.columns(num_columns)
            row_recs = recommendations[i:i + num_columns]
            for j, rec in enumerate(row_recs):
                with cols[j]:
                    # Escape HTML to prevent injection vulnerabilities
                    title = html.escape(rec.get('title', 'N/A'))
                    author = html.escape(rec.get('author', 'N/A'))
                    try:
                        rating_text = f"{float(rec.get('avg_rating')):.2f}"
                    except (ValueError, TypeError):
                        rating_text = "N/A"
                    # Render the book card using HTML
                    card_html = f"""
                    <div class="book-card">
                        <div> <h4 title="{title}">{title}</h4> <p class="author" title="by {author}">by {author}</p> </div>
                        <div> <p class="rating">⭐ {rating_text} Average Rating</p> </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.error("No recommendations available! Read more books...")

# Page for updating reading progress for a book
def show_update_progress():
    st.title("📈 Update Reading Progress")
    st.markdown("<br>", unsafe_allow_html=True)

    # Initialize session state for progress update functionality
    if 'progress_book_input' not in st.session_state:
        st.session_state.progress_book_input = ""

    # Auto-load book if an ID is passed from another page
    if st.session_state.progress_book_input and 'progress_book' not in st.session_state:
        book_id = st.session_state.progress_book_input.strip().upper()
        if is_valid_book_id_format(book_id):
            book = get_book_details(st.session_state.user_id, book_id)
            if book:
                st.session_state.progress_book = book
                st.session_state.progress_book_id = book_id

    st.session_state.setdefault("progress_deadline_input", None)
    st.session_state.setdefault("progress_rating_input", "None")

    # Callback to find a book for updating progress
    def _handle_find_book():
        st.session_state.pop("progress_book", None)
        st.session_state.pop("progress_book_id", None)
        book_id = st.session_state.progress_book_input.strip().upper()
        if not book_id:
            st.warning("Please enter a Book ID!")
            return
        if not is_valid_book_id_format(book_id):
            st.error("Invalid Book ID format!")
            st.session_state.progress_book_input = ""
            return
        book = get_book_details(st.session_state.user_id, book_id)
        if not book:
            st.error("Book not found!")
            st.session_state.progress_book_input = ""
        elif not book.get('total_pages'):
            st.error("Total pages not found! Please edit the book to add total pages first...")
            st.session_state.progress_book_input = ""
        else:
            st.session_state.progress_book = book
            st.session_state.progress_book_id = book_id
            st.session_state.progress_status_select = None

    # Callback to handle the progress update logic
    def _handle_update_progress():
        book = st.session_state.progress_book
        new_status = st.session_state.progress_status_select
        
        if not new_status:
            st.warning("Please select a new status to update!")
            return

        total_pages = int(book.get('total_pages', 1))
        pages_read = int(book.get('pages_read', 0)) # Default to current pages read
        deadline = st.session_state.progress_deadline_input
        rating_display = st.session_state.progress_rating_input

        # Update pages read based on the new status
        if new_status.lower() == "completed":
            pages_read = total_pages
        elif new_status.lower() == "to-read":
            pages_read = 0
        elif new_status.lower() == "reading":
            pages_read = st.session_state.progress_pages_read_input

        if pages_read > total_pages:
            st.error("Pages read cannot be greater than total pages!")
            return

        # Extract numeric value from the rating string (e.g., "5⭐")
        rating_value = None if rating_display == "Choose an option" else int(str(rating_display)[0])

        # Prepare the data payload for the database update
        progress_data = {
            'total_pages': total_pages, 'pages_read': pages_read, 'status': new_status.lower(),
            'deadline': deadline.strftime("%Y-%m-%d") if deadline else book.get('deadline'),
            'rating': rating_value
        }

        # Attempt to update the book progress in the database
        try:
            success, percent = update_book_progress_in_db(
                st.session_state.user_id, st.session_state.progress_book_id, progress_data)
            if success:
                st.success("Progress updated successfully!")
                _handle_cancel_progress() # Clear the form
                st.session_state.trigger_progress_rerun = True
        except Exception:
            st.error(f"Error updating progress...")

    # Callback to cancel the update and clear the form
    def _handle_cancel_progress():
        st.session_state.pop("progress_book", None)
        st.session_state.pop("progress_book_id", None)
        st.session_state.progress_book_input = ""

    # UI for finding a book to update
    st.text_input("Book ID", placeholder="e.g. B1001", key="progress_book_input")
    st.button("🔍 Find Book", on_click=_handle_find_book)

    # If a book is found, display the update form
    if 'progress_book' in st.session_state:
        book = st.session_state.progress_book
        st.success(f"Updating: {book.get('title')} by {book.get('author')}")

        new_status = st.selectbox("New Status", [None, "To-read", "Reading", "Completed"],
                                  format_func=lambda x: "Choose an option" if x is None else x,
                                  key="progress_status_select")

        # Conditionally display inputs based on the selected status
        if new_status:
            total_pages = int(book.get('total_pages', 1))
            
            # Only show "Pages Read" input if status is "Reading"
            if new_status == "Reading":
                current_pages_read = int(book.get('pages_read', 0))
                st.number_input("Pages Read", min_value=0, max_value=total_pages,
                                value=current_pages_read, key="progress_pages_read_input")

            # Rating selector
            star_options = ["Choose an option", "1⭐", "2⭐", "3⭐", "4⭐", "5⭐"]
            current_rating_val = book.get('rating')
            current_rating_str = f"{current_rating_val}⭐" if current_rating_val in [1,2,3,4,5] else "Choose an option"
            st.selectbox("Rating (optional)", star_options, index=star_options.index(current_rating_str),
                         key="progress_rating_input")

            # Deadline selector
            current_deadline = book.get('deadline')
            deadline_val = datetime.strptime(current_deadline, "%Y-%m-%d").date() if current_deadline else None
            st.date_input("Deadline (optional)", value=deadline_val, key="progress_deadline_input")

            # Action buttons
            _, col2, _, col4, _ = st.columns(5)
            with col2:
                st.button("📈 Update", on_click=_handle_update_progress, type="primary", use_container_width=True)
            with col4:
                st.button("❌ Cancel", on_click=_handle_cancel_progress, use_container_width=True)

# Page to view upcoming and overdue book deadlines
def show_view_deadlines():
    st.title("⏰ Your Reading Deadlines")
    st.markdown("<br>", unsafe_allow_html=True)
    
    books = get_all_books_for_user(st.session_state.user_id)
    today = date.today()
    upcoming, overdue = [], []
    
    # Categorize books based on their deadline status
    for book in books:
        deadline_str = book.get('deadline')
        if not deadline_str: continue
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            if book.get('status', '').lower() != 'completed':
                book_info = (book.get('title'), deadline_str, deadline)
                if deadline >= today:
                    upcoming.append(book_info)
                else:
                    overdue.append(book_info)
        except:
            continue
    
    # Display the categorized lists in two columns
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📅 Upcoming Deadlines")
        st.markdown("<br>", unsafe_allow_html=True)
        if upcoming:
            for title, date_str, _ in sorted(upcoming, key=lambda x: x[2]):
                st.success(f"• {title}: Due by {date_str}")
        else:
            st.success("No upcoming deadlines!")
    with col2:
        st.subheader("⚠️ Overdue Books")
        st.markdown("<br>", unsafe_allow_html=True)
        if overdue:
            for title, date_str, _ in sorted(overdue, key=lambda x: x[2]):
                st.error(f"• {title}: Was due on {date_str}")
        else:
            st.error("No overdue books!")

# Page to archive completed books
def show_archive_book():
    st.title("📦 Archive Book")
    st.markdown("<br>", unsafe_allow_html=True)

    # Callback to find a book to archive
    def _handle_find_archive_book():
        if 'archive_book' in st.session_state: del st.session_state.archive_book
        if 'archive_book_id' in st.session_state: del st.session_state.archive_book_id

        book_id = st.session_state.archive_book_input.strip().upper()
        if not book_id:
            st.warning("Please enter a Book ID!")
            return
        if not is_valid_book_id_format(book_id):
            st.error("Invalid Book ID format!")
            st.session_state.archive_book_input = ""
        else:
            book = get_book_details(st.session_state.user_id, book_id)
            if not book:
                st.error("Book not found!")
                st.session_state.archive_book_input = ""
            elif book.get('status', '').lower() != 'completed':
                st.error("This book is not marked as 'Completed' yet!")
                st.session_state.archive_book_input = ""
            elif book.get('archived') is True:
                st.info("This book has already been archived!")
                st.session_state.archive_book_input = ""
            else:
                st.session_state.archive_book = book
                st.session_state.archive_book_id = book_id

    # Callback to confirm and execute the archiving
    def _handle_confirm_archive():
        try:
            success = archive_single_book_in_db(st.session_state.user_id, st.session_state.archive_book_id)
            if success:
                st.success("Book archived successfully!")
                del st.session_state.archive_book
                del st.session_state.archive_book_id
                st.session_state.archive_book_input = ""
        except Exception:
            st.error(f"Error archiving book...")

    # Callback to cancel the archiving operation
    def _handle_cancel_archive():
        del st.session_state.archive_book
        del st.session_state.archive_book_id
        st.session_state.archive_book_input = ""

    # UI for finding a book to archive
    st.text_input("Book ID", placeholder="e.g. B1001", key="archive_book_input")
    st.button("🔍 Find Book", on_click=_handle_find_archive_book)

    # If a book is found, show confirmation buttons
    if 'archive_book' in st.session_state:
        book = st.session_state.archive_book
        st.warning(f"Archiving: {book.get('title')} by {book.get('author')}")
        _, col2, _, col4, _ = st.columns(5)
        with col2:
            st.button("📦 Archive", type="primary", on_click=_handle_confirm_archive)
        with col4:
            st.button("❌ Cancel", on_click=_handle_cancel_archive)

    # Fetch and display the list of all archived books
    archived_books = [book for book in get_all_books_for_user(st.session_state.user_id) if book.get('archived') is True]

    st.title("📚 Archived Books")
    st.markdown("<br>", unsafe_allow_html=True)
    if archived_books:
        st.success(f"Showing {len(archived_books)} archived book(s)...")

        # Display each archived book in an expander
        for book in archived_books:
            title = book.get("title", "N/A")
            author = book.get("author", "N/A")
            book_id = book.get("book_id", "N/A")

            with st.expander(f"📘 {title} by {author}"):
                col1, col2, col3 = st.columns([2.5, 1.5, 1.5])
                with col1: # Book details
                    st.markdown(f"Status: {book.get('status', 'N/A').capitalize()}")
                    st.markdown(f"Genre: {book.get('genre', 'None')}")
                    rating_display = f"{book.get('rating')} ⭐" if book.get('rating') not in [None, 'None'] else "None"
                    st.markdown(f"Rating: {rating_display}")
                    progress = float(book.get("progress_percent", 0))
                    st.progress(progress / 100, text=f"Progress: {book.get('pages_read', 0)}/{book.get('total_pages', 1)} pages ({progress:.1f}%)")
                with col2: # Metadata
                    st.markdown(f"Book ID: `{book_id}`")
                    tags_list = book.get("tags", [])
                    st.markdown("Tags:" if tags_list else "Tags: N/A")
                    if tags_list:
                        st.markdown("\n".join([f"- `{tag}`" for tag in tags_list]))
                with col3: # Unarchive button
                    if st.button(f"📤 Unarchive", key=f"unarchive_{book_id}", use_container_width=True):
                        try:
                            success = unarchive_single_book_in_db(st.session_state.user_id, book_id)
                            if success:
                                st.success(f"Book `{book_id}` unarchived successfully!")
                                st.rerun()
                            else:
                                st.error("Unarchive failed!")
                        except Exception:
                            st.error(f"Error...")
    else:
        st.info("No archived books found!")

# Displays a list of books as expandable cards with edit/update/delete buttons
def display_books_table_edit(books):
    if not books:
        st.info("No books to display!")
        return

    for book in books:
        title = book.get("title", "N/A")
        author = book.get("author", "N/A")
        book_id = book.get("book_id", "N/A")

        with st.expander(f"📘 {title} by {author}"):
            col1, col2, col3 = st.columns([2.5, 1.5, 1.5])
            with col1: # Book details
                st.markdown(f"Status: {book.get('status', 'N/A').capitalize()}")
                st.markdown(f"Genre: {book.get('genre', 'None')}")
                rating_display = f"{book.get('rating')} ⭐" if book.get('rating') not in [None, 'None'] else "None"
                st.markdown(f"Rating: {rating_display}")
                progress_float = float(book.get("progress_percent", 0.0))
                st.progress(progress_float / 100, text=f"Progress: {book.get('pages_read', 0)}/{book.get('total_pages', 1)} pages ({progress_float:.1f}%)")
            with col2: # Metadata
                st.markdown(f"Book ID: `{book_id}`")
                tags_list = book.get("tags", [])
                st.markdown("Tags:" if tags_list else "Tags: None")
                if tags_list:
                    st.markdown("\n".join([f"- `{tag}`" for tag in tags_list]))
            with col3: # Action buttons that redirect to other pages
                if st.button(f"✏️ Edit", key=f"edit_{book_id}", use_container_width=True):
                    st.session_state.edit_book_input = book_id
                    st.session_state.selected_page = "edit"
                    st.rerun()
                if st.button(f"📈 Update", key=f"progress_{book_id}", use_container_width=True):
                    st.session_state.progress_book_input = book_id
                    st.session_state.selected_page = "progress"
                    st.rerun()
                if st.button(f"🗑️ Delete", key=f"delete_{book_id}", use_container_width=True):
                    st.session_state.delete_book_input = book_id
                    st.session_state.selected_page = "delete"
                    st.rerun()

# Displays a list of books as expandable cards (view-only version)
def display_books_table(books):
    if not books:
        st.info("No books to display!")
        return

    for book in books:
        title = book.get("title", "N/A")
        author = book.get("author", "N/A")
        book_id = book.get("book_id", "N/A")

        with st.expander(f"📘 {title} by {author}"):
            col1, col2 = st.columns([2, 1])
            with col1: # Book details
                st.markdown(f"Status: {book.get('status', 'N/A').capitalize()}")
                st.markdown(f"Genre: {book.get('genre', 'None')}")
                rating_display = f"{book.get('rating')} ⭐" if book.get('rating') not in [None, 'None'] else "None"
                st.markdown(f"Rating: {rating_display}")
                progress_float = float(book.get("progress_percent", 0.0))
                st.progress(progress_float / 100, text=f"Progress: {book.get('pages_read', 0)}/{book.get('total_pages', 1)} pages ({progress_float:.1f}%)")
            with col2: # Metadata
                st.markdown(f"Book ID: `{book_id}`")
                tags_list = book.get("tags", [])
                st.markdown("Tags:" if tags_list else "Tags: None")
                if tags_list:
                    st.markdown("\n".join([f"- `{tag}`" for tag in tags_list]))

# Main function to control the application flow
def main():
    # Show a loading screen during login
    if st.session_state.get("show_loading_screen", False):
        st.markdown('<div class="loading-text">🔄 Logging you in, please wait...</div>', unsafe_allow_html=True)
        with st.spinner("Loading Dashboard..."):
            import time
            time.sleep(2.5) # Simulate loading time
        st.session_state.show_loading_screen = False
        st.rerun()
    # Show a logout screen during logout
    elif st.session_state.get("show_logout_screen", False):
        st.markdown('<div class="loading-text">👋 Logging you out, see you soon...</div>', unsafe_allow_html=True)
        with st.spinner("Clearing session..."):
            import time
            time.sleep(2) # Simulate clearing session
        st.session_state.clear()
        st.rerun()
    # If not logged in, show the login page
    elif not st.session_state.logged_in:
        show_login()
    # If logged in, show the main application
    else:
        main_app()

# Entry point of the script
if __name__ == "__main__":
    main()