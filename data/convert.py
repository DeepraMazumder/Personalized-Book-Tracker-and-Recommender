import pandas as pd
# Import ast to safely convert strings to Python objects.
import ast
# Import json to read and write JSON files.
import json

# Try to read the CSV file into a DataFrame.
try:
    df = pd.read_csv('data/book_dataset.csv')
# Handle the case where the file is not found.
except FileNotFoundError:
    print("‼️  File not found...")
    exit()

def parse_genres(genres_str):
    """
    Converts a string list of genres into a real Python list.
    """
    try:
        # Safely parse the genre string into a list.
        return ast.literal_eval(genres_str)
    # Return an empty list if parsing fails.
    except (ValueError, SyntaxError):
        return []

# Convert genre strings into actual lists.
df['Genres'] = df['Genres'].apply(parse_genres)

# Convert the DataFrame to a list of dictionaries.
records = df.to_dict(orient='records')

# Set the path for the output JSON file.
output_json_path = 'data/book_dataset.json'
# Open the file to write the JSON data.
with open(output_json_path, 'w', encoding='utf-8') as f:
    # Write the records list to the JSON file.
    json.dump(records, f, ensure_ascii=False, indent=2)

# Print success message after conversion.
print(f"✅ File successfully converted to JSON!")