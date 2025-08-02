import streamlit as st
import pandas as pd
from datetime import timedelta
import plotly.express as px
from db_module.dynamo_handler import get_all_books_for_user
from dashboard.report_generator import generate_pdf_summary # Import from the new file

# This file now contains only the dashboard display logic
def show_dashboard():
    st.title("📊 Dashboard")
    
    st.markdown("""
        <style>
            .stDownloadButton>button { display: block; margin: 0 auto; }
            .st-emotion-cache-z5fcl4 { border-left: 1px solid #3c3d44; padding-left: 20px; }
        </style>
        """, unsafe_allow_html=True)

    books = get_all_books_for_user(st.session_state.user_id)
    if not books:
        st.info("📭 No books found. Start by adding your first book!")
        return

    # --- Data Processing ---
    df = pd.DataFrame(books)
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    completed_df = df[df['status'] == 'completed'].copy()
    
    # --- 1. Key Metrics Section ---
    st.subheader("🚀 Your Reading Snapshot")
    
    pending_books = len(df[df['status'] == 'to-read'])
    avg_rating = df['rating'].mean()
    approaching_deadlines = 0
    if 'deadline' in df.columns:
        df['deadline'] = pd.to_datetime(df['deadline'], errors='coerce')
        approaching_deadlines = len(df[
            (df['status'] != 'completed') & (df['deadline'] >= pd.to_datetime('today')) &
            (df['deadline'] <= pd.to_datetime('today') + timedelta(days=7))
        ])
    
    avg_books_per_month = 0
    if not completed_df.empty and 'timestamp' in completed_df.columns:
        completed_df['timestamp'] = pd.to_datetime(completed_df['timestamp'])
        completed_df['month_year'] = completed_df['timestamp'].dt.to_period('M')
        monthly_counts = completed_df['month_year'].value_counts()
        if not monthly_counts.empty:
            avg_books_per_month = monthly_counts.mean()

    metrics = {
        "Total Books": len(df), "Completed": len(completed_df), "Pending Books": pending_books,
        "Average Rating": f"{avg_rating:.2f}" if pd.notna(avg_rating) else "N/A",
        "Avg. Books/Month": f"{avg_books_per_month:.1f}",
        "Approaching Deadlines": approaching_deadlines
    }

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("📚 Total Books", metrics["Total Books"])
    with col2: st.metric("✅ Completed", metrics["Completed"])
    with col3: st.metric("📋 Pending Books", metrics["Pending Books"])
    
    col4, col5, col6 = st.columns(3)
    with col4: st.metric("⭐ Average Rating", metrics["Average Rating"])
    with col5: st.metric("🗓️ Avg. Books/Month", metrics["Avg. Books/Month"])
    with col6: st.metric("❗ Approaching Deadlines", metrics["Approaching Deadlines"])
    
    st.divider()

    # --- 2. Reading Trends & Stats ---
    st.subheader("📈 Reading Trends & Stats")
    
    col1, col2 = st.columns([0.6, 0.4])
    with col1:
        st.markdown("##### Your Favorite Genres")
        genre_counts = df['genre'].str.lower().value_counts().nlargest(10)
        if not genre_counts.empty:
            capitalized_labels = genre_counts.index.str.capitalize()
            fig = px.bar(genre_counts, x=capitalized_labels, y=genre_counts.values,
                         labels={'x': 'Genre', 'y': 'Number of Books'},
                         color=capitalized_labels, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add genres to your books to see trends here!")

    with col2:
        st.markdown("##### Books per Genre")
        if not genre_counts.empty:
            genre_df = genre_counts.reset_index()
            genre_df.columns = ['Genre', 'Count']
            genre_df['Genre'] = genre_df['Genre'].str.capitalize()
            genre_df.index = range(1, len(genre_df) + 1)
            genre_df.index.name = "Sl.No"
            st.dataframe(genre_df.style.set_properties(**{'text-align': 'center'}), use_container_width=True)
        else:
            st.info("No genre stats to show.")
            
    st.divider()

    # --- 3. Your Library Section ---
    st.subheader("📖 Your Library")
    
    top_rated_books = df.dropna(subset=['rating']).sort_values('rating', ascending=False).head(5)
    with st.expander("🏆 Your Top 5 Rated Books"):
        if not top_rated_books.empty:
            for _, book in top_rated_books.iterrows():
                st.markdown(f"- **{book['title']}** by {book['author']} (Rating: {book['rating']})")
        else:
            st.write("Rate your books to see your top 5!")

    pdf_data = generate_pdf_summary(st.session_state.user_name, books, metrics, genre_df, top_rated_books)
    st.download_button(
        label="📥 Download Reading Summary (PDF)",
        data=pdf_data,
        file_name=f"{st.session_state.user_name}_Reading_Summary.pdf",
        mime="application/pdf"
    )