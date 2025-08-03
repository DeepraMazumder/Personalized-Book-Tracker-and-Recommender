import pandas as pd
import re

# --- 1. Load Initial Data ---
try:
    # Load dataset from CSV into a DataFrame.
    df = pd.read_csv('data/goodreads_data.csv')
    # Remove the first column (index).
    df.drop(columns=df.columns[0], inplace=True)
except Exception as e:
    # Handle errors during file loading (e.g., FileNotFoundError).
    print(f"Error loading CSV...")
    exit()

# --- 2. Initial Column and Row Cleanup ---
# Drop unnecessary columns from the dataset.
df.drop(columns=['Description', 'Num_Ratings', 'URL'], inplace=True)
# Remove rows with missing book titles.
df.dropna(subset=['Book'], inplace=True)

# --- 3. Clean Book Titles ---
# Remove parenthetical info (e.g., series details) from book titles.
df['Book'] = df['Book'].str.replace(r'\s*\([^)]*\)\s*', '', regex=True).str.strip()

# --- 4. Fix Character Encoding Issues (Mojibake) ---
def fix_common_mojibake(text):
    """Fix common encoding issues from misinterpreted UTF-8 characters."""
    # Return non-string values unchanged.
    if not isinstance(text, str):
        return text
    # Map of corrupted characters to their corrected versions.
    replacements = {
        'â€™': '’', 'â€œ': '“', 'â€': '”', 'â€”': '—', 'â€¦': '…',
        'Ã©': 'é', 'Ã¡': 'á', 'Ã¶': 'ö', 'Ã¼': 'ü', 'Ã±': 'ñ'
    }
    # Replace corrupted characters with correct ones.
    for wrong, right in replacements.items():
        text = text.replace(wrong, right)
    return text

# Apply mojibake fixes to 'Book' and 'Author' columns.
for col in ['Book', 'Author']:
    if col in df.columns:
        df[col] = df[col].apply(fix_common_mojibake)

# --- 5. Remove Extraneous Characters ---
# Remove double quotes from 'Book' and 'Author' columns.
for col in ['Book', 'Author']:
    if col in df.columns and df[col].dtype == 'object':
        df[col] = df[col].str.replace('"', '', regex=False)

# --- 6. Filter Out Corrupted or Non-English Rows ---
def is_mostly_non_ascii(s):
    """Check if a string contains mostly non-ASCII characters."""
    # Flag non-string values for removal.
    if not isinstance(s, str):
        return True
    # Flag rows without English alphabet characters.
    if not re.search(r'[a-zA-Z]', s):
        return True
    return False

# Keep rows where 'Book' titles are not flagged as non-ASCII.
df = df[~df['Book'].apply(is_mostly_non_ascii)]

# --- 7. Final Deduplication and Cleaning ---
# Remove any duplicate rows in the DataFrame.
df.drop_duplicates(inplace=True)
# Strip extra whitespace from 'Book' titles.
df['Book'] = df['Book'].str.strip()
# Remove rows with null or empty book titles.
df.dropna(subset=['Book'], inplace=True)
df = df[df['Book'] != '']

# --- 8. Save Cleaned Data ---
# Save the cleaned DataFrame to a new CSV file without the index column.
df.to_csv('data/book_dataset.csv', index=False)

# --- 9. Confirmation ---
# Print a success message and show a sample of the cleaned data.
print("Preprocessing is complete!")
print("Here's a sample of the cleaned data:")
print(df.head(10))