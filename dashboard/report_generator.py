from fpdf import FPDF  # PDF generation library

def generate_pdf_summary(user_name, books, metrics, top_rated_books, genre_counts):
    """
    Generates a PDF summary of the user's reading data with custom formatting.
    """
    pdf = FPDF(orientation='P', unit='mm', format='A4')  # Initialize A4 portrait PDF
    pdf.add_page()
    
    # --- Heading ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f'Reading Summary for {user_name}', 0, 1, 'C')

    # --- Signature ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, '~ The SmartReads Team', 0, 1, 'R')  # Right-aligned signature
    pdf.ln(5)

    # --- Section 1: Reading Statistics ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, 'Reading Statistics', 0, 1, 'C')

    # Table dimensions
    pdf.set_font("Arial", '', 12)
    metric_cell_width = 90
    value_cell_width = 30
    cell_height = 8
    table_width = metric_cell_width + value_cell_width
    start_x = (pdf.w - table_width) / 2  # Center the table

    snapshot_metrics = [
        ("Total Books", metrics.get('Total Books', 'N/A')),
        ("Completed Books", metrics.get('Completed Books', 'N/A')),
        ("Pending Books", metrics.get('Pending Books', 'N/A')),
        ("Average Rating", metrics.get('Average Rating', 'N/A')),
        ("Average Books/Month", metrics.get('Average Books/Month', 'N/A')),
        ("Approaching Deadlines", metrics.get('Approaching Deadlines', 'N/A'))
    ]

    # Render snapshot metrics table
    for label, value in snapshot_metrics:
        pdf.set_x(start_x)
        pdf.cell(metric_cell_width, cell_height, label, 1, 0, 'C')
        pdf.cell(value_cell_width, cell_height, str(value), 1, 1, 'C')

    pdf.ln(5)

    # --- Section 2: Favorite Genres ---
    if not genre_counts.empty:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, 'Top Favorite Genres', 0, 1, 'C')

        header_widths = [20, 90, 40]
        fav_table_width = sum(header_widths)
        fav_start_x = (pdf.w - fav_table_width) / 2

        pdf.set_x(fav_start_x)
        pdf.cell(header_widths[0], cell_height, 'Rank', 1, 0, 'C')
        pdf.cell(header_widths[1], cell_height, 'Genre', 1, 0, 'C')
        pdf.cell(header_widths[2], cell_height, 'Book Count', 1, 1, 'C')

        pdf.set_font("Arial", '', 12)
        rank = 1
        for genre, count in genre_counts.nlargest(3).items():
            pdf.set_x(fav_start_x)
            pdf.cell(header_widths[0], cell_height, str(rank), 1, 0, 'C')
            pdf.cell(header_widths[1], cell_height, genre.capitalize(), 1, 0, 'C')
            pdf.cell(header_widths[2], cell_height, str(count), 1, 1, 'C')
            rank += 1

        pdf.ln(5)

        # Books per Genre Breakdown
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
        pdf.cell(0, 10, 'Top Rated Books', 0, 1, 'L')
        pdf.set_font("Arial", '', 12)
        for _, book in top_rated_books.iterrows():
            # Encode text safely for PDF
            title = book['title'].encode('latin-1', 'replace').decode('latin-1')
            author = book['author'].encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 6, f"  * {title} by {author} ({book['rating']})", 0, 1)

    pdf.ln(5)

    # --- Section 4: Full Book List ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, 'Full Book List', 0, 1, 'L')
    pdf.set_font("Arial", '', 12)

    for book in books:
        # Safely retrieve and format book details
        title = book.get('title', 'N/A').encode('latin-1', 'replace').decode('latin-1')
        author = book.get('author', 'N/A').encode('latin-1', 'replace').decode('latin-1')
        status = book.get('status', 'N/A').capitalize()
        rating = book.get('rating', 'N/A')
        rating_display = f"{rating}" if rating and str(rating) != 'N/A' else "N/A"
        line = f"* {title} by {author}, Status: {status}, Rating: {rating_display}"
        pdf.multi_cell(0, 6, line, 0, 'L')  # Multi-line cell for wrapping long lines

    return pdf.output(dest='S').encode('latin1')  # Return PDF as byte string