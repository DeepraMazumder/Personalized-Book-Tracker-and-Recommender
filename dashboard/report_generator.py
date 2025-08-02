from fpdf import FPDF

# This file now contains only the PDF generation logic.
def generate_pdf_summary(user_name, books, metrics, genre_df, top_rated_books):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    pdf.cell(0, 10, f'Reading Summary for {user_name}', 0, 1, 'C')
    pdf.ln(10)

    # --- Section 1: Reading Snapshot (Key Metrics) ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, 'Your Reading Snapshot', 0, 1)
    pdf.set_font("Arial", '', 10)
    
    stat_items = [
        f"- Total Books: {metrics.get('Total Books', 'N/A')}",
        f"- Books Completed: {metrics.get('Completed', 'N/A')}",
        f"- Pending Books: {metrics.get('Pending Books', 'N/A')}",
        f"- Average Rating: {metrics.get('Average Rating', 'N/A')}",
        f"- Avg. Books/Month: {metrics.get('Avg. Books/Month', 'N/A')}",
        f"- Approaching Deadlines: {metrics.get('Approaching Deadlines', 'N/A')}"
    ]
    
    for i in range(0, len(stat_items), 2):
        pdf.cell(95, 5, stat_items[i])
        if i + 1 < len(stat_items):
            pdf.cell(95, 5, stat_items[i+1])
        pdf.ln()
    pdf.ln(5)

    # --- Section 2: Reading Stats (Genres) ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, 'Reading Stats', 0, 1)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, 'Books per Genre:', 0, 1)
    pdf.set_font("Arial", '', 10)
    if not genre_df.empty:
        for _, row in genre_df.iterrows():
            pdf.cell(0, 5, f"  - {row['Genre']}: {row['Count']} book(s)", 0, 1)
    else:
        pdf.cell(0, 5, "  - No genre data available.", 0, 1)
    pdf.ln(5)

    # --- Section 3: Top Rated Books ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, 'Your Top Rated Books', 0, 1)
    pdf.set_font("Arial", '', 10)
    if not top_rated_books.empty:
        for _, book in top_rated_books.iterrows():
            pdf.cell(0, 5, f"- {book['title']} by {book['author']} (Rating: {book['rating']})", 0, 1)
    else:
        pdf.cell(0, 5, "  - Rate your books to see your top 5!", 0, 1)
    pdf.ln(5)

    # --- Section 4: Full Book List ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, 'Your Full Book List', 0, 1)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 8, 'Title', 1, 0, 'C')
    pdf.cell(50, 8, 'Author', 1, 0, 'C')
    pdf.cell(25, 8, 'Status', 1, 0, 'C')
    pdf.cell(20, 8, 'Rating', 1, 1, 'C')
    
    pdf.set_font("Arial", '', 9)
    for book in books:
        pdf.cell(90, 8, book.get('title', 'N/A')[:40], 1)
        pdf.cell(50, 8, book.get('author', 'N/A')[:25], 1)
        pdf.cell(25, 8, book.get('status', 'N/A').capitalize(), 1)
        pdf.cell(20, 8, str(book.get('rating', 'N/A')), 1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin1')