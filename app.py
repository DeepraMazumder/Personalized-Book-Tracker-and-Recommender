import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import re
from decimal import Decimal, InvalidOperation
import html
import plotly.express as px
from fpdf import FPDF
import io
import tempfile
import calendar
import plotly.graph_objects as go

# Import your existing modules
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

# Page configuration
st.set_page_config(
    page_title="SmartReads",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Utility functions
def is_valid_book_id_format(book_id):
    pattern = re.compile(r'^B\d{4}$')
    return bool(pattern.match(book_id))

def is_valid_user_id_format(user_id):
    pattern = re.compile(r'^U\d{4}$')
    return bool(pattern.match(user_id))

def format_book_for_display(book):
    """Format book data for display"""
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

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def show_login():
    # --- Sidebar Content ---
    # All the informational content is now placed in the native sidebar
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

        st.markdown(
            """
            <style>
                .sidebar-footer {
                    position: fixed;
                    bottom: 20px;
                    left: 20px;
                    width: 270px; /* Adjust width as needed */
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

    # --- Main Page Content (Login Forms) ---
    st.markdown("<h1 style='text-align: center;'>📚 Welcome to SmartReads!</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns([0.5, 0.5])
        
    with col1:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🔄 Returning User")
        user_id_input = st.text_input("Enter your User ID (e.g. U1001):", key="login_user_id")
        st.markdown("<br>", unsafe_allow_html=True)
        
        _, login_button_col, _ = st.columns([1, 1, 1])
        with login_button_col:
            # The button is placed here, and its clicked state is captured.
            login_clicked = st.button("Login", key="login_btn", use_container_width=True)

        if login_clicked:
            if user_id_input:
                user_id_upper = user_id_input.strip().upper()
                if is_valid_user_id_format(user_id_upper):
                    user_details = get_user_details(user_id_upper)
                    if user_details:
                        st.session_state.user_id = user_id_upper
                        st.session_state.user_name = user_details.get("name", "User")
                        st.session_state.logged_in = True
                        st.session_state.show_loading_screen = True
                        st.rerun()
                    else:
                        st.error("User ID not found!")
                else:
                    st.error("Invalid User ID format!")
            else:
                st.error("Please enter a User ID!")
        
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("✨ New User")
        name_input = st.text_input("Enter your name:", key="register_name")
        # --- NEW: Email input field ---
        email_input = st.text_input("Enter your email:", key="register_email")
        st.markdown("<br>", unsafe_allow_html=True)

        _, create_account_button_col, _ = st.columns([1, 1, 1])
        with create_account_button_col:
            # The button is placed here, and its clicked state is captured.
            create_account_clicked = st.button("Create Account", key="register_btn", use_container_width=True)

        if create_account_clicked:
            name = name_input.strip()
            email = email_input.strip()

            # --- MODIFIED: Validate both name and email ---
            if name and email:
                # You might want to add more robust email validation
                if "@" in email and "." in email:
                    user_id = generate_user_id()
                    # --- MODIFIED: Pass email to your registration function ---
                    # Ensure your register_user function is updated to accept and store the email
                    register_user(user_id, name, email)

                    st.success("Account created! Check your email for a welcome message with your User ID.")
                    st.info("Please confirm the subscription in the first email from AWS to receive future notifications.")

                    # Log the user in immediately after registration
                    st.session_state.user_id = user_id
                    st.session_state.user_name = name
                    st.session_state.logged_in = True
                    st.session_state.show_loading_screen = True
                    st.rerun()
                else:
                    st.error("Please enter a valid email address!")
            else:
                st.error("Please enter both your name and email!")  

def main_app():
    # Sidebar
    with st.sidebar:
        st.title(f"👋 Hello, {st.session_state.user_name}!")
        st.write(f"**User ID:** {st.session_state.user_id}")

        # Make logout button full-width
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.show_logout_screen = True
            st.rerun()

        st.divider()

        st.markdown("### 📍 Navigate to:")

        nav_options = [
            ("📊 Dashboard", "dashboard"),
            ("➕ Add Book", "add"),
            ("✏️ Edit Book", "edit"),
            ("🗑️ Delete Book", "delete"),
            ("🔍 Search Books", "search"),
            ("🔎 Filter Books", "filter"),
            ("📖 Reading History", "history"),
            ("💡 Recommendations", "recommend"),
            ("📈 Update Progress", "progress"),
            ("⏰ View Deadlines", "deadlines"),
            ("📦 Archive Book", "archive")
        ]

        # Initialize selected page
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = "dashboard"

        # Full-width buttons for each navigation option
        for label, value in nav_options:
            if st.button(label, use_container_width=True):
                st.session_state.selected_page = value
                st.rerun()

    # Page rendering
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

def generate_pdf_summary(user_name, books, metrics, top_rated_books, genre_counts):
    """
    Generates a PDF summary of the user's reading data with custom formatting.
    
    IMPORTANT: Remember to pass the 'genre_counts' Series from your dashboard.
    """
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # --- Heading ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f'Reading Summary for {user_name}', 0, 1, 'C')
    pdf.ln(5)

    # --- Section 1: Reading Snapshot ---
    pdf.set_font("Arial", 'B', 12)
    # MODIFIED: Left-aligned the subheading
    pdf.cell(0, 10, 'Reading Statistics', 0, 1, 'C')
    
    # MODIFIED: Re-structured into a 6x2 table
    pdf.set_font("Arial", '', 12)
    metric_cell_width = 90
    value_cell_width = 30
    cell_height = 8
    table_width = metric_cell_width + value_cell_width
    start_x = (pdf.w - table_width) / 2 # Center the table

    snapshot_metrics = [
        ("Total Books", metrics.get('Total Books', 'N/A')),
        ("Completed Books", metrics.get('Completed Books', 'N/A')),
        ("Pending Books", metrics.get('Pending Books', 'N/A')),
        ("Average Rating", metrics.get('Average Rating', 'N/A')),
        ("Average Books/Month", metrics.get('Average Books/Month', 'N/A')),
        ("Approaching Deadlines", metrics.get('Approaching Deadlines', 'N/A'))
    ]

    for label, value in snapshot_metrics:
        pdf.set_x(start_x)
        # Table content remains center-aligned
        pdf.cell(metric_cell_width, cell_height, label, 1, 0, 'C')
        pdf.cell(value_cell_width, cell_height, str(value), 1, 1, 'C')
    
    pdf.ln(5)
    
    if not genre_counts.empty:
        # -- Favorite Genres Table --
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, 'Top 3 Favorite Genres', 0, 1, 'C')
        
        header_widths = [20, 90, 40]
        fav_table_width = sum(header_widths)
        fav_start_x = (pdf.w - fav_table_width) / 2

        pdf.set_x(fav_start_x)
        # Table content remains center-aligned
        pdf.cell(header_widths[0], cell_height, 'Rank', 1, 0, 'C')
        pdf.cell(header_widths[1], cell_height, 'Genre', 1, 0, 'C')
        pdf.cell(header_widths[2], cell_height, 'Book Count', 1, 1, 'C')
        
        pdf.set_font("Arial", '', 12)
        rank = 1
        for genre, count in genre_counts.nlargest(3).items():
            pdf.set_x(fav_start_x)
            # Table content remains center-aligned
            pdf.cell(header_widths[0], cell_height, str(rank), 1, 0, 'C')
            pdf.cell(header_widths[1], cell_height, genre.capitalize(), 1, 0, 'C')
            pdf.cell(header_widths[2], cell_height, str(count), 1, 1, 'C')
            rank += 1
        pdf.ln(5)

        # -- Books per Genre (%) --
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, 'Books per Genre:', 0, 1, 'L')
        pdf.set_font("Arial", '', 12)
        total_genre_books = genre_counts.sum()
        for genre, count in genre_counts.items():
            percentage = (count / total_genre_books) * 100
            pdf.cell(0, 6, f"  * {genre.capitalize()}: {percentage:.1f}%", 0, 1)
    pdf.ln(5)

    # --- Section 3: Top Rated Books ---    
    if not top_rated_books.empty:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, 'Top 5 Rated Books', 0, 1, 'L')
        pdf.set_font("Arial", '', 12)
        for _, book in top_rated_books.iterrows():
            title = book['title'].encode('latin-1', 'replace').decode('latin-1')
            author = book['author'].encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 6, f"  * {title} by {author} ({book['rating']})", 0, 1)
    pdf.ln(5)

    # --- Section 4: Full Book List ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, 'Full Book List', 0, 1, 'L')
    pdf.set_font("Arial", '', 12)
    
    for book in books:
        title = book.get('title', 'N/A').encode('latin-1', 'replace').decode('latin-1')
        author = book.get('author', 'N/A').encode('latin-1', 'replace').decode('latin-1')
        status = book.get('status', 'N/A').capitalize()
        rating = book.get('rating', 'N/A')
        
        rating_display = f"{rating}" if rating and str(rating) != 'N/A' else "N/A"
        
        line = f"* {title} by {author}, Status: {status}, Rating: {rating_display}"
        # MODIFIED: Used multi_cell for text wrapping
        pdf.multi_cell(0, 6, line, 0, 'L')
        
    pdf.ln(10) # Add extra space before the signature

    # --- Signature ---
    # MODIFIED: Added a final signature
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, '~ The SmartReads Team', 0, 1, 'R')

    return pdf.output(dest='S').encode('latin1')

def show_dashboard():
    st.title("📊 Dashboard")
    
    st.markdown("""
        <style>
            .stDownloadButton>button { display: block; margin: 0 auto; }
            .st-emotion-cache-z5fcl4 { border-left: 1px solid #3c3d44; padding-left: 20px; }
            .calendar-container {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
            }
        </style>
        """, unsafe_allow_html=True)

    books = get_all_books_for_user(st.session_state.user_id)
    df = pd.DataFrame(books)
    
    # --- 1. Key Metrics Section (Book Stats) ---
    st.subheader("🚀 Reading Snapshot")
    
    # Initialize all metrics to 0 or default values
    total_books = 0
    completed = 0
    pending_books = 0
    avg_rating = 0.0
    approaching_deadlines = 0
    avg_books_per_month = 0.0
    top_rated_books = pd.DataFrame()

    # If books exist, calculate the actual metrics
    if not df.empty:
        total_books = len(df)
        
        if 'status' in df.columns:
            completed_df = df[df['status'] == 'completed'].copy()
            completed = len(completed_df)
            pending_books = len(df[df['status'].str.lower() != 'completed'])
            
            if not completed_df.empty and 'timestamp' in completed_df.columns:
                completed_df['timestamp'] = pd.to_datetime(completed_df['timestamp'])
                completed_df['month_year'] = completed_df['timestamp'].dt.to_period('M')
                monthly_counts = completed_df['month_year'].value_counts()
                if not monthly_counts.empty:
                    avg_books_per_month = monthly_counts.mean()
        
        if 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
            avg_rating = df['rating'].mean()
            top_rated_books = df.dropna(subset=['rating']).sort_values('rating', ascending=False).head(5)
        
        if 'deadline' in df.columns:
            df['deadline'] = pd.to_datetime(df['deadline'], errors='coerce')
            approaching_deadlines = len(df[
                (df['status'].str.lower() != 'completed') & 
                (df['deadline'].notna()) &
                (df['deadline'].dt.date >= date.today())
            ])

    # Format metrics for display
    metrics = {
        "Total Books": total_books,
        "Completed Books": completed,
        "Pending Books": pending_books,
        "Average Rating": f"{avg_rating:.1f}" if pd.notna(avg_rating) else "0.0",
        "Average Books/Month": f"{avg_books_per_month:.1f}",
        "Approaching Deadlines": approaching_deadlines
    }

    # Display metrics regardless of whether books exist
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1: st.metric("📚 Total Books", metrics["Total Books"])
    with col2: st.metric("✅ Completed Books", metrics["Completed Books"])
    with col3: st.metric("⚠️ Pending Books", metrics["Pending Books"])
    
    col4, col5, col6 = st.columns([1, 1, 1])
    with col4: st.metric("⭐ Average Rating", metrics["Average Rating"])
    with col5: st.metric("🗓️ Average Books/Month", metrics["Average Books/Month"])
    with col6: st.metric("‼️ Approaching Deadlines", metrics["Approaching Deadlines"])
    
    st.divider()

    # If no books, show the message and stop the rest of the dashboard from rendering.
    if not books:
        st.info("To access your statistics, please add a book!")
        return

    # --- 2. Reading Trends & Stats (Book Stats) ---
    st.subheader("📈 Reading Trends & Stats")
    
    col1, col2 = st.columns([0.5, 0.5])

    with col1:
        st.markdown("##### Top 3 Favorite Genres")
        if 'genre' in df.columns and not df['genre'].dropna().empty:
            genre_counts = df['genre'].str.lower().value_counts().nlargest(3)
            capitalized_labels = genre_counts.index.str.capitalize()
            fig = px.bar(
                genre_counts, x=capitalized_labels, y=genre_counts.values,
                labels={'x': 'Genre', 'y': 'Number of Books'},
                color=capitalized_labels, color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(showlegend=False)
            fig.update_traces(hovertemplate=None)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add genres to your books to see trends here!")

    with col2:
        st.markdown("##### Books per Genre")
        if 'genre' in df.columns and not df['genre'].dropna().empty:
            # MODIFIED: Removed .nlargest(3) to include all genres
            genre_counts = df['genre'].str.lower().value_counts()
            capitalized_labels = genre_counts.index.str.capitalize()
            pie_fig = px.pie(
                names=capitalized_labels, values=genre_counts.values,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            pie_fig.update_traces(textinfo='percent+label', hoverinfo='none')
            st.plotly_chart(pie_fig, use_container_width=True)
        else:
            st.info("No genre stats to show!")

    st.divider()

    # --- 3. Your Library Section ---
    st.subheader("📖 Library")
    
    with st.expander("🏆 Top 5 Rated Books"):
        if not top_rated_books.empty:
            for _, book in top_rated_books.iterrows():
                st.markdown(f"- {book['title']} by {book['author']} ({book['rating']} ⭐)")
        else:
            st.write("Rate your books to see your top 5!")

    if 'genre' in df.columns and not df['genre'].dropna().empty:
        genre_counts = df['genre'].str.lower().value_counts()
    else:
        genre_counts = pd.Series() # Pass an empty series if no genres

    pdf_data = generate_pdf_summary(
        st.session_state.user_name, 
        books, 
        metrics, 
        top_rated_books,
        genre_counts  # <-- Pass the new data here
    )
    
    st.download_button(
        label="📥 Download Reading Summary (PDF)",
        data=pdf_data,
        file_name=f"{st.session_state.user_name}_Reading_Summary.pdf",
        mime="application/pdf"
    )

def show_add_book():
    st.title("➕ Add New Book")

    # --- State Initialization ---
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

    # --- Callback Functions ---
    def _handle_add_book():
        title = st.session_state.add_title.strip()
        author = st.session_state.add_author.strip()
        total_pages = st.session_state.add_total_pages
        pages_read = st.session_state.add_pages_read

        # ✅ Validations
        if not title or not author:
            st.error("Title and Author are required fields!")
            return

        if total_pages is None or str(total_pages).strip() == "" or int(total_pages) <= 0:
            st.error("Total Pages must be greater than or equal to 1!")
            return

        if pages_read > total_pages:
            st.error("Pages read cannot be greater than total pages!")
            return

        book_data = {
            "title": title,
            "author": author,
            "genre": st.session_state.add_genre.strip() if st.session_state.add_genre else None,
            "rating": Decimal(str(st.session_state.add_rating)) if st.session_state.add_rating else None,
            "status": st.session_state.add_status.lower(),
            "tags": st.session_state.add_tags.strip(),
            "total_pages": int(total_pages),
            "pages_read": int(pages_read)
        }

        try:
            success = add_book_to_db(st.session_state.user_id, book_data)
            if success:
                st.success("Book added successfully!")
                _handle_cancel_add()
            else:
                st.error("This book already exists in your reading list!")
        except Exception:
            st.error("An unexpected error occurred...")

    def _handle_cancel_add():
        st.session_state.add_title = ""
        st.session_state.add_author = ""
        st.session_state.add_genre = ""
        st.session_state.add_rating = None
        st.session_state.add_status = "To-read"
        st.session_state.add_tags = ""
        st.session_state.add_total_pages = 1
        st.session_state.add_pages_read = 0

    # --- UI Elements ---
    st.markdown("""
        <style>
            .stButton>button { display: block; margin: 0 auto; }
        </style>
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
        # Removed min_value to allow manual validation
        st.number_input("Total Pages *", key="add_total_pages", step=1, format="%d")
        st.number_input("Pages Read", min_value=0, key="add_pages_read", step=1, format="%d")

    # --- Real-time Validation ---
    pages_read_invalid = st.session_state.add_pages_read > st.session_state.add_total_pages
    if pages_read_invalid:
        st.warning("Pages read cannot be greater than total pages!")

    # --- Action Buttons ---
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.button("✅ Add", on_click=_handle_add_book, type="primary", disabled=pages_read_invalid)
    with btn_col2:
        st.button("❌ Cancel", on_click=_handle_cancel_add)

def show_edit_book():
    st.title("✏️ Edit Book")
    st.markdown("<br>", unsafe_allow_html=True)

    if 'edit_book_input' not in st.session_state:
        st.session_state.edit_book_input = ""

    # Auto-fetch if book ID is pre-filled but book not yet loaded
    if st.session_state.edit_book_input and 'edit_book' not in st.session_state:
        book_id = st.session_state.edit_book_input.strip().upper()
        if is_valid_book_id_format(book_id):
            book = get_book_details(st.session_state.user_id, book_id)
            if book:
                st.session_state.edit_book = book
                st.session_state.edit_book_id = book_id

    # --- Callbacks ---

    def _on_field_change():
        """Resets the input widget's state when the field to edit is changed."""
        if 'edit_new_value_input' in st.session_state:
            del st.session_state['edit_new_value_input']

    def _handle_find_book():
        # Clear previous edit session
        st.session_state.pop("edit_book", None)
        st.session_state.pop("edit_book_id", None)
        _on_field_change()  # Also clear the input value

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

    def _handle_update_book():
        """Handles the logic to update a book field."""
        # Get current state from session
        field = st.session_state.edit_field_select
        new_value = st.session_state.edit_new_value_input
        book = st.session_state.edit_book
        
        final_value = new_value
        updated_fields = {}

        # --- Step 1: Sanitize text input ---
        if field in ["title", "author", "genre", "tags"]:
            if isinstance(new_value, str) and not new_value.strip():
                final_value = None

        # --- Step 2: Validate required fields ---
        if field in ["title", "author"] and final_value is None:
            st.error(f"{field.capitalize()} is a required field!")
            return

        # --- Step 3: Process value and create the update payload ---
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
                
                new_percent = round(Decimal(pages_read) / Decimal(total_pages_val) * 100, 2)
                updated_fields = {'total_pages': total_pages_val, 'progress_percent': new_percent}
            
            else:
                # For all other fields (title, author, etc.)
                updated_fields = {field: final_value}

        except (ValueError, TypeError, InvalidOperation):
            st.error(f"Invalid value provided for {field}. Please check your input.")
            return

        # --- Step 4: Call the database handler to commit changes ---
        try:
            edit_book(st.session_state.user_id, st.session_state.edit_book_id, updated_fields)
            st.success("Book edited successfully!")
            # Clean up the session state
            st.session_state.pop("edit_book", None)
            st.session_state.pop("edit_book_id", None)
            st.session_state.edit_book_input = ""

        except Exception as e:
            st.error(f"Update failed. Database error: {e}")
            return

    def _handle_cancel_edit():
        st.session_state.pop("edit_book", None)
        st.session_state.pop("edit_book_id", None)
        st.session_state.edit_book_input = ""

    # --- UI Elements ---
    st.text_input("Book ID", placeholder="e.g. B1001", key="edit_book_input")
    st.button("🔍 Find Book", on_click=_handle_find_book)

    if 'edit_book' in st.session_state:
        book = st.session_state.edit_book
        st.success(f"Editing: {book.get('title')} by {book.get('author')}")

        # MODIFIED: Removed "rating" from the options
        field_options = {
            "title": "Title", "author": "Author", "genre": "Genre",
            "tags": "Tags", "total_pages": "Total Pages"
        }

        field = st.selectbox(
            "Field to Edit",
            options=[None] + list(field_options.keys()),
            format_func=lambda key: "Choose an option" if key is None else field_options[key],
            key="edit_field_select",
            on_change=_on_field_change
        )

        if field:
            current_value = book.get(field, "")

            # MODIFIED: Removed the entire UI block for editing the rating
            if field == "total_pages":
                st.number_input(
                    "New Total Pages",
                    placeholder=f"Current: {current_value or 'Not Set'}",
                    key="edit_new_value_input",
                    step=1,
                    format="%d"
                )
            else:
                st.text_input(
                    f"New {field_options[field]}",
                    placeholder=f"Current: {current_value or 'Not Set'}",
                    key="edit_new_value_input"
                )

            _, col2, _, col4, _ = st.columns(5)
            with col2:
                st.button("💾 Edit", on_click=_handle_update_book, type="primary", use_container_width=True)
            with col4:
                st.button("❌ Cancel", on_click=_handle_cancel_edit, use_container_width=True)

def show_delete_book():
    st.title("🗑️ Delete Book")
    st.markdown("<br>", unsafe_allow_html=True)

    if 'delete_book_input' not in st.session_state:
        st.session_state.delete_book_input = ""

    # 🔁 Auto-load book if Book ID is passed from display_books_table_edit
    if st.session_state.delete_book_input and 'delete_book' not in st.session_state:
        book_id = st.session_state.delete_book_input.strip().upper()
        if is_valid_book_id_format(book_id):
            book = get_book_details(st.session_state.user_id, book_id)
            if book:
                st.session_state.delete_book = book
                st.session_state.delete_book_id = book_id


    # --- Callbacks ---
    # These functions run before the page rerenders, allowing safe state changes.

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
    
    def _handle_book_delete():
        try:
            delete_book(st.session_state.user_id, st.session_state.delete_book_id)
            st.success("Book deleted successfully!")
            del st.session_state.delete_book
            del st.session_state.delete_book_id
            st.session_state.delete_book_id_input = ""
        except Exception:
            st.error(f"Error deleting book...")

    # New callback specifically for the Cancel button
    def _handle_cancel_delete():
        # Clear all related session state variables
        if 'delete_book' in st.session_state:
            del st.session_state.delete_book
        if 'delete_book_id' in st.session_state:
            del st.session_state.delete_book_id
            
        # Clear both the manual input and the redirect input state
        st.session_state.delete_book_id_input = ""
        st.session_state.delete_book_input = ""


    # --- UI Elements ---

    st.text_input(
        "Book ID",
        placeholder="e.g. B1001",
        key="delete_book_id_input"
    )

    st.button("🔍 Find Book", on_click=_handle_find_book)

    if 'delete_book' in st.session_state:
        book = st.session_state.delete_book
        st.warning(f"Deleting: {book.get('title')} by {book.get('author')}")

        _, col2, _, col4, _ = st.columns(5)
        with col2:
            st.button(
                "🗑️ Delete",
                type="primary",
                on_click=_handle_book_delete,
                use_container_width=True
            )
        with col4:
            # The Cancel button now uses its own dedicated on_click callback
            st.button("❌ Cancel", on_click=_handle_cancel_delete, use_container_width=True)

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
        results = filter_books(
            st.session_state.user_id,
            genre.strip() if genre.strip() else None,
            str(rating) if rating else None,
            status.lower() if status else None
        )
        
        if results:
            st.success(f"Found {len(results)} book(s)...")
            display_books_table(results)
        else:
            st.info("No books match your filters!")

def show_reading_history():
    st.title("📖 Reading History")
    st.markdown("<br>", unsafe_allow_html=True)
    
    history = get_user_history(st.session_state.user_id)

    if history:
        # Sort by Book ID (e.g., "B1001", "B1002", ...)
        history_sorted = sorted(history, key=lambda b: b.get("book_id", ""))
        st.success(f"Showing {len(history_sorted)} book(s) from your history...")
        display_books_table_edit(history_sorted)
    else:
        st.info("No reading history found!")

def show_recommendations():
    st.title("💡 Personalized Recommendations")
    st.markdown("<br>", unsafe_allow_html=True)

    # Card styles: fixed height for visual consistency + clamped title
    card_css = """
    <style>
        .book-card {
            background-color: #262730;
            border: 1px solid #3c3d44;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            height: 200px; /* Uniform height */
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: border-color 0.3s;
            overflow: hidden; /* Prevent content from spilling out */
        }
        .book-card:hover { border-color: #4A90E2; }

        .book-card h4 {
            font-size: 1.1rem;
            font-weight: 600;
            color: #FAFAFA;
            margin: 0 0 10px 0;

            /* Clamp title to 2 lines with ellipsis */
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
            word-wrap: break-word;
        }

        .book-card .author {
            font-style: italic;
            font-size: 0.95rem;
            color: #A0A0A5;
            margin: 0;

            /* Keep author to one line with ellipsis if needed */
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }

        .book-card .rating {
            font-size: 0.9rem;
            color: #FFC107;
            font-weight: 500;
            margin-top: 10px;
        }
    </style>
    """
    st.markdown(card_css, unsafe_allow_html=True)

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
                    raw_title = rec.get('title', 'N/A')
                    raw_author = rec.get('author', 'N/A')
                    avg_rating = rec.get('avg_rating')

                    title = html.escape(raw_title)
                    author = html.escape(raw_author)

                    try:
                        rating_text = f"{float(avg_rating):.2f}"
                    except (ValueError, TypeError):
                        rating_text = "N/A"

                    card_html = f"""
                    <div class="book-card">
                        <div>
                            <h4 title="{title}">{title}</h4>
                            <p class="author" title="by {author}">by {author}</p>
                        </div>
                        <div>
                            <p class="rating">⭐ {rating_text} Average Rating</p>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.error("No recommendations available! Read more books...")

def show_update_progress():
    st.title("📈 Update Reading Progress")
    st.markdown("<br>", unsafe_allow_html=True)

    if 'progress_book_input' not in st.session_state:
        st.session_state.progress_book_input = ""

    # Auto-load book if passed from edit table
    if st.session_state.progress_book_input and 'progress_book' not in st.session_state:
        book_id = st.session_state.progress_book_input.strip().upper()
        if is_valid_book_id_format(book_id):
            book = get_book_details(st.session_state.user_id, book_id)
            if book:
                st.session_state.progress_book = book
                st.session_state.progress_book_id = book_id

    # State Initialization (removed progress_status_select)
    st.session_state.setdefault("progress_deadline_input", None)
    st.session_state.setdefault("progress_rating_input", "None")

    # --- Callback: Find Book ---
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
            # Reset status selection when a new book is found
            st.session_state.progress_status_select = None

    # --- Callback: Update Progress ---
    def _handle_update_progress():
        book = st.session_state.progress_book
        new_status = st.session_state.progress_status_select
        
        # Prevent update if no status is selected
        if not new_status:
            st.warning("Please select a new status to update!")
            return

        total_pages = int(book.get('total_pages', 1))
        # Default pages_read to current value, then update based on status
        pages_read = int(book.get('pages_read', 0))
        deadline = st.session_state.progress_deadline_input
        rating_display = st.session_state.progress_rating_input

        if new_status.lower() == "completed":
            pages_read = total_pages
        elif new_status.lower() == "to-read":
            pages_read = 0
        elif new_status.lower() == "reading":
            pages_read = st.session_state.progress_pages_read_input

        if pages_read > total_pages:
            st.error("Pages read cannot be greater than total pages!")
            return

        # Extract numeric part from rating
        if rating_display == "Choose an option":
            rating_value = None
        else:
            try:
                rating_value = int(str(rating_display)[0])
            except:
                st.warning("Invalid rating format.")
                return

        progress_data = {
            'total_pages': total_pages,
            'pages_read': pages_read,
            'status': new_status.lower(),
            'deadline': deadline.strftime("%Y-%m-%d") if deadline else book.get('deadline'),
            'rating': rating_value
        }

        try:
            success, percent = update_book_progress_in_db(
                st.session_state.user_id,
                st.session_state.progress_book_id,
                progress_data
            )
            if success:
                st.success("Progress updated successfully!")
                _handle_cancel_progress()
                st.session_state.trigger_progress_rerun = True
        except Exception:
            st.error(f"Error updating progress...")

    # --- Callback: Cancel ---
    def _handle_cancel_progress():
        st.session_state.pop("progress_book", None)
        st.session_state.pop("progress_book_id", None)
        st.session_state.progress_book_input = ""

    # --- UI ---
    st.text_input("Book ID", placeholder="e.g. B1001", key="progress_book_input")
    st.button("🔍 Find Book", on_click=_handle_find_book)

    if 'progress_book' in st.session_state:
        book = st.session_state.progress_book
        st.success(f"Updating: {book.get('title')} by {book.get('author')}")

        # Add placeholder to the status selectbox. The UI below will only appear after a selection.
        new_status = st.selectbox(
            "New Status",
            [None, "To-read", "Reading", "Completed"],
            format_func=lambda x: "Choose an option" if x is None else x,
            key="progress_status_select"
        )

        # This entire block only runs AFTER the user selects a status from the dropdown above.
        if new_status:
            total_pages = int(book.get('total_pages', 1))

            # The "Pages Read" input is ONLY shown if the selected status is "Reading".
            if new_status == "Reading":
                current_pages_read = int(book.get('pages_read', 0))
                st.number_input("Pages Read", min_value=0,
                                max_value=total_pages,
                                value=current_pages_read,
                                key="progress_pages_read_input")

            # The rest of the widgets (Rating, Deadline, Buttons) are shown for any selected status.
            
            # Rating Selector
            star_options = ["Choose an option", "1⭐", "2⭐", "3⭐", "4⭐", "5⭐"]
            current_rating_val = book.get('rating')
            current_rating_str = f"{current_rating_val}⭐" if current_rating_val in [1,2,3,4,5] else "Choose an option"
            st.selectbox("Rating (optional)", star_options, 
                         index=star_options.index(current_rating_str),
                         key="progress_rating_input")

            # Deadline Selector
            current_deadline = book.get('deadline')
            deadline_val = datetime.strptime(current_deadline, "%Y-%m-%d").date() if current_deadline else None
            st.date_input("Deadline (optional)", value=deadline_val, key="progress_deadline_input")

            # Action Buttons
            _, col2, _, col4, _ = st.columns(5)
            with col2:
                st.button("📈 Update", on_click=_handle_update_progress, type="primary", use_container_width=True)
            with col4:
                st.button("❌ Cancel", on_click=_handle_cancel_progress, use_container_width=True)

def show_view_deadlines():
    st.title("⏰ Your Reading Deadlines")
    st.markdown("<br>", unsafe_allow_html=True)
    
    books = get_all_books_for_user(st.session_state.user_id)
    today = date.today()
    upcoming, overdue = [], []
    
    for book in books:
        deadline_str = book.get('deadline')
        if not deadline_str:
            continue
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Upcoming Deadlines")
        st.markdown("<br>", unsafe_allow_html=True)
        if upcoming:
            # Use st.info() to display each item in a blue box
            for title, date_str, _ in sorted(upcoming, key=lambda x: x[2]):
                st.success(f"• {title}: Due by {date_str}")
        else:
            # Use st.success() to match the style of the "No overdue books!" message
            st.success("No upcoming deadlines!")
    
    with col2:
        st.subheader("⚠️ Overdue Books")
        st.markdown("<br>", unsafe_allow_html=True)
        if overdue:
            for title, date_str, _ in sorted(overdue, key=lambda x: x[2]):
                st.error(f"• {title}: Was due on {date_str}")
        else:
            st.error("No overdue books!")

def show_archive_book():
    st.title("📦 Archive Book")
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Callbacks for Archive ---
    def _handle_find_archive_book():
        # Clear previous state
        if 'archive_book' in st.session_state:
            del st.session_state.archive_book
        if 'archive_book_id' in st.session_state:
            del st.session_state.archive_book_id

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

    def _handle_cancel_archive():
        del st.session_state.archive_book
        del st.session_state.archive_book_id
        st.session_state.archive_book_input = ""

    # --- UI Elements ---
    st.text_input("Book ID", placeholder="e.g. B1001", key="archive_book_input")
    st.button("🔍 Find Book", on_click=_handle_find_archive_book)

    if 'archive_book' in st.session_state:
        book = st.session_state.archive_book
        st.warning(f"Archiving: {book.get('title')} by {book.get('author')}")

        _, col2, _, col4, _ = st.columns(5)
        with col2:
            st.button("📦 Archive", type="primary", on_click=_handle_confirm_archive)
        with col4:
            st.button("❌ Cancel", on_click=_handle_cancel_archive)

    archived_books = [
        book for book in get_all_books_for_user(st.session_state.user_id)
        if book.get('archived') is True
    ]

    st.title("📚 Archived Books")
    st.markdown("<br>", unsafe_allow_html=True)

    if archived_books:
        st.success(f"Showing {len(archived_books)} archived book(s)...")

        for book in archived_books:
            title = book.get("title", "N/A")
            author = book.get("author", "N/A")
            book_id = book.get("book_id", "N/A")

            with st.expander(f"📘 {title} by {author}"):
                col1, col2, col3 = st.columns([2.5, 1.5, 1.5])

                with col1:
                    st.markdown(f"Status: {book.get('status', 'N/A').capitalize()}")
                    st.markdown(f"Genre: {book.get('genre', 'None')}")
                    rating = book.get('rating')
                    rating_display = f"{rating} ⭐" if rating not in [None, 'None'] else "None"
                    st.markdown(f"Rating: {rating_display}")
                    progress = book.get("progress_percent", 0)
                    pages_read = book.get("pages_read", 0)
                    total_pages = book.get("total_pages", 1)
                    progress_float = float(progress)
                    st.progress(progress_float / 100, text=f"Progress: {pages_read}/{total_pages} pages ({progress_float:.1f}%)")

                with col2:
                    st.markdown(f"Book ID: `{book_id}`")
                    tags_list = book.get("tags", [])
                    if tags_list:
                        st.markdown("Tags:")
                        tags_md = "\n".join([f"- `{tag}`" for tag in tags_list])
                        st.markdown(tags_md)
                    else:
                        st.markdown("Tags: N/A")

                with col3:
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

def display_books_table_edit(books):
    """Display books in a clean, card-style collapsible format (used in Reading History, Search, etc.)"""
    if not books:
        st.info("No books to display!")
        return

    for book in books:
        title = book.get("title", "N/A")
        author = book.get("author", "N/A")
        book_id = book.get("book_id", "N/A")

        with st.expander(f"📘 {title} by {author}"):
            col1, col2, col3 = st.columns([2.5, 1.5, 1.5])  # Adjust width ratios as needed

            with col1:
                st.markdown(f"Status: {book.get('status', 'N/A').capitalize()}")
                st.markdown(f"Genre: {book.get('genre', 'None')}")
                rating = book.get('rating')
                rating_display = f"{rating} ⭐" if rating not in [None, 'None'] else "None"
                st.markdown(f"Rating: {rating_display}")

                progress = book.get("progress_percent", 0)
                pages_read = book.get("pages_read", 0)
                total_pages = book.get("total_pages", 1)
                try:
                    progress_float = float(progress)
                except:
                    progress_float = 0.0

                st.progress(progress_float / 100, text=f"Progress: {pages_read}/{total_pages} pages ({progress_float:.1f}%)")

            with col2:
                st.markdown(f"Book ID: `{book_id}`")

                tags_list = book.get("tags", [])
                if tags_list:
                    st.markdown("Tags:")
                    tags_md = "\n".join([f"- `{tag}`" for tag in tags_list])
                    st.markdown(tags_md)
                else:
                    st.markdown("Tags: None")

            with col3:
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

def display_books_table(books):
    """Display books in a clean, card-style collapsible format (used in Reading History, Search, etc.)"""
    if not books:
        st.info("No books to display!")
        return

    for book in books:
        title = book.get("title", "N/A")
        author = book.get("author", "N/A")
        book_id = book.get("book_id", "N/A")

        with st.expander(f"📘 {title} by {author}"):
            col1, col2 = st.columns([2, 1])  # Wider left column for details

            with col1:
                st.markdown(f"Status: {book.get('status', 'N/A').capitalize()}")
                st.markdown(f"Genre: {book.get('genre', 'None')}")
                rating = book.get('rating')
                rating_display = f"{rating} ⭐" if rating not in [None, 'None'] else "None"
                st.markdown(f"Rating: {rating_display}")

                progress = book.get("progress_percent", 0)
                pages_read = book.get("pages_read", 0)
                total_pages = book.get("total_pages", 1)
                try:
                    progress_float = float(progress)
                except:
                    progress_float = 0.0

                st.progress(progress_float / 100, text=f"Progress: {pages_read}/{total_pages} pages ({progress_float:.1f}%)")

            with col2:
                st.markdown(f"Book ID: `{book_id}`")

                tags_list = book.get("tags", [])
                if tags_list:
                    st.markdown("Tags:")
                    tags_md = "\n".join([f"- `{tag}`" for tag in tags_list])
                    st.markdown(tags_md)
                else:
                    st.markdown("Tags: None")

def main():
    if st.session_state.get("show_loading_screen", False):
        st.markdown('<div class="loading-text">🔄 Logging you in, please wait...</div>', unsafe_allow_html=True)
        with st.spinner("Loading Dashboard..."):
            import time
            time.sleep(2.5)
        st.session_state.show_loading_screen = False
        st.rerun()

    elif st.session_state.get("show_logout_screen", False):
        st.markdown('<div class="loading-text">👋 Logging you out, see you soon...</div>', unsafe_allow_html=True)
        with st.spinner("Clearing session..."):
            import time
            time.sleep(2)
        st.session_state.clear()
        st.rerun()

    elif not st.session_state.logged_in:
        show_login()
    else:
        main_app()

if __name__ == "__main__":
    main()