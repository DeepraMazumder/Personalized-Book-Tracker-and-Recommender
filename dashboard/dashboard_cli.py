import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px

from reading_tracker.tracker import get_all_books_for_user
from dashboard.report_generator import generate_pdf_summary

def show_dashboard():
    st.title("📊 Dashboard")

    # Custom CSS styling for buttons and layout
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

    books = get_all_books_for_user(st.session_state.user_id)  # Fetch user's books
    df = pd.DataFrame(books)  # Convert to DataFrame for easier processing

    # --- 1. Key Metrics Section ---
    st.subheader("🚀 Reading Snapshot")

    # Initialize metric values
    total_books = 0
    completed = 0
    pending_books = 0
    avg_rating = 0.0
    approaching_deadlines = 0
    avg_books_per_month = 0.0
    top_rated_books = pd.DataFrame()

    # --- Compute metrics if books exist ---
    if not df.empty:
        total_books = len(df)

        # Calculate completed & pending books
        if 'status' in df.columns:
            completed_df = df[df['status'] == 'completed'].copy()
            completed = len(completed_df)
            pending_books = len(df[df['status'].str.lower() != 'completed'])

            # Monthly reading trend
            if not completed_df.empty and 'timestamp' in completed_df.columns:
                completed_df['timestamp'] = pd.to_datetime(completed_df['timestamp'])
                completed_df['month_year'] = completed_df['timestamp'].dt.to_period('M')
                monthly_counts = completed_df['month_year'].value_counts()
                if not monthly_counts.empty:
                    avg_books_per_month = monthly_counts.mean()

        # Average rating and top 5 rated books
        if 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
            avg_rating = df['rating'].mean()
            top_rated_books = df.dropna(subset=['rating']).sort_values('rating', ascending=False).head(5)

        # Upcoming deadlines
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

    # Display key metrics in a 2-row layout
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1: st.metric("📚 Total Books", metrics["Total Books"])
    with col2: st.metric("✅ Completed Books", metrics["Completed Books"])
    with col3: st.metric("⚠️ Pending Books", metrics["Pending Books"])

    col4, col5, col6 = st.columns([1, 1, 1])
    with col4: st.metric("⭐ Average Rating", metrics["Average Rating"])
    with col5: st.metric("🗓️ Average Books/Month", metrics["Average Books/Month"])
    with col6: st.metric("‼️ Approaching Deadlines", metrics["Approaching Deadlines"])

    st.divider()

    # Stop if user has no books
    if not books:
        st.info("To access your statistics, please add a book!")
        return

    # --- 2. Reading Trends & Stats ---
    st.subheader("📈 Reading Trends & Stats")

    col1, col2 = st.columns([0.5, 0.5])

    with col1:
        st.markdown("##### Top 3 Favorite Genres")
        if 'genre' in df.columns and not df['genre'].dropna().empty:
            genre_counts = df['genre'].str.lower().value_counts().nlargest(3)
            capitalized_labels = genre_counts.index.str.capitalize()
            fig = px.bar(
                genre_counts,
                x=capitalized_labels,
                y=genre_counts.values,
                labels={'x': 'Genre', 'y': 'Number of Books'},
                color=capitalized_labels,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(showlegend=False)
            fig.update_traces(hovertemplate=None)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add genres to your books to see trends here!")

    with col2:
        st.markdown("##### Books per Genre")
        if 'genre' in df.columns and not df['genre'].dropna().empty:
            genre_counts = df['genre'].str.lower().value_counts()
            capitalized_labels = genre_counts.index.str.capitalize()
            pie_fig = px.pie(
                names=capitalized_labels,
                values=genre_counts.values,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            pie_fig.update_traces(textinfo='percent+label', hoverinfo='none')
            st.plotly_chart(pie_fig, use_container_width=True)
        else:
            st.info("No genre stats to show!")

    st.divider()

    # --- 3. Your Library Section ---
    st.subheader("📖 Library")

    # Top 5 rated books section
    with st.expander("🏆 Top 5 Rated Books"):
        if not top_rated_books.empty:
            for _, book in top_rated_books.iterrows():
                st.markdown(f"- {book['title']} by {book['author']} ({book['rating']} ⭐)")
        else:
            st.write("Rate your books to see your top 5!")

    # Genre count for PDF summary
    if 'genre' in df.columns and not df['genre'].dropna().empty:
        genre_counts = df['genre'].str.lower().value_counts()
    else:
        genre_counts = pd.Series()  # Empty if no genres

    # --- Generate and allow downloading of the reading summary PDF ---
    pdf_data = generate_pdf_summary(
        st.session_state.user_name,
        books,
        metrics,
        top_rated_books,
        genre_counts
    )

    st.download_button(
        label="📥 Download Reading Summary (PDF)",
        data=pdf_data,
        file_name=f"{st.session_state.user_name}_Reading_Summary.pdf",
        mime="application/pdf"
    )