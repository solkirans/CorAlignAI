import csv
import os
import sys
from io import StringIO
import time
from openai import OpenAI

# ======= CONFIGURATION SETTINGS =======
# CSV filename to update (the file that will be updated with movement scores)
CSV_FILENAME = "YogaMuscleList.csv"

# Muscle CSV file containing the muscle information (6 columns, 251 rows)
MUSCLE_FILENAME = "MuscleList.csv"

# API key file (make sure this file exists and contains your API key)
API_KEY_FILENAME = "ApiKey.txt"
if not os.path.exists(API_KEY_FILENAME):
    print(f"Error: API key file '{API_KEY_FILENAME}' not found at {os.path.abspath(API_KEY_FILENAME)}")
    sys.exit(1)
with open(API_KEY_FILENAME, "r", encoding="utf-8") as key_file:
    API_KEY = key_file.read().strip()

# OpenAI API settings
API_MODEL = "gpt-4o"        # Use an available model; change if necessary
API_TEMPERATURE = 0.2       # Lower temperature for deterministic output

# Adjustable parameters to enable/disable printing of prompt and API responses
PRINT_API_RESPONSE = True   # Set to False to disable printing the full API response
PRINT_PROMPT = True         # Set to False to disable printing the prompt (including muscle context)
# ======= END CONFIGURATION SETTINGS =======

client = OpenAI(api_key=API_KEY)

def load_csv_as_dicts(filename):
    """Load a CSV file as a list of dictionaries with stripped header keys."""
    data = []
    with open(filename, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        headers = [h.strip() for h in reader.fieldnames if h is not None]
        for row in reader:
            new_row = {key.strip(): (value.strip() if isinstance(value, str) else value)
                       for key, value in row.items() if key is not None}
            data.append(new_row)
    return data, headers

def write_csv_from_dicts(filename, data, headers):
    """Write the list of dictionaries back to a CSV file using the given headers."""
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def get_value_from_row(row, key):
    """
    Try to get the value from the row using the given key.
    If not found, try the lowercase version; otherwise, return "N/A".
    """
    if key in row and row[key]:
        return row[key]
    elif key.lower() in row and row[key.lower()]:
        return row[key.lower()]
    else:
        return "N/A"

def get_muscle_context(data):
    """
    Build a context string containing exactly six columns from the muscle CSV.
    These columns are: Number, Type, PrimaryRegion, Side, Name, OtherRegions.
    """
    columns = ["Number", "Type", "PrimaryRegion", "Side", "Name", "OtherRegions"]
    context_lines = [", ".join(columns)]
    for row in data:
        values = [get_value_from_row(row, col) for col in columns]
        context_lines.append(", ".join(values))
    muscle_context = "\n".join(context_lines)
    if PRINT_PROMPT:
        print("Extracted Muscle Context from MuscleList.csv:")
        print(muscle_context)
    if len(data) == 0 or all(all(get_value_from_row(row, col) == "N/A" for col in columns) for row in data):
        print("WARNING: Muscle context appears to be empty.")
    return muscle_context

def extract_csv_block(api_text):
    """
    Given the API's returned text, extract only the CSV-formatted part.
    This function looks for the first line containing "ItemNumber" and then
    includes subsequent lines that contain commas.
    """
    lines = api_text.splitlines()
    csv_lines = []
    found_header = False
    for line in lines:
        if not found_header:
            if "ItemNumber" in line:
                found_header = True
                csv_lines.append(line)
        else:
            # If line is empty or does not contain a comma, we assume CSV block has ended.
            if line.strip() == "" or "," not in line:
                break
            csv_lines.append(line)
    return "\n".join(csv_lines)

def call_openai_api_for_movement(movement_number, muscle_context):
    """
    Build the prompt for a given movement number (including muscle context),
    print the prompt, call the OpenAI API using the new interface, and return the API's response text.
    """
    prompt = f"""Below is the list of muscles from the MuscleList.csv file (6 columns, 251 rows):
{muscle_context}

Now, I want you to analyze yoga movements and create a score for every muscle (using the muscle numbers from the above data) according to how big is the effect on that muscle. Use numbers between -1 and 1. Cover as many muscles as possible for the movement. If the movement stretches a muscle, use positive numbers. If the movement trains (contracts or tightens) that muscle, use negative values.
You must give the output of your analysis in CSV format. Do not output a sample; output the full CSV. If you hit the output limit, inform me with bold and big text.

Consider that even in simple standing positions, a scoliosis patient must engage muscles for balance and breathing; so even small activations (e.g., 0.05) should be reflected. Adjust the scaling of other movements accordingly.

Run analyze only for movement number {movement_number}."""
    
    if PRINT_PROMPT:
        print(f"\nSending the following prompt to the API for movement {movement_number}:\n{prompt}\n")
    
    print(f"--- Processing movement number {movement_number} ---")
    print("Calling OpenAI API...")
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant specialized in yoga anatomy analysis."},
                {"role": "user", "content": prompt}
            ],
            model=API_MODEL,
            temperature=API_TEMPERATURE
        )
    except Exception as e:
        error_message = str(e)
        if "404" in error_message or "model_not_found" in error_message:
            print(f"Error calling OpenAI API for movement {movement_number}:")
            print("The model '{0}' does not exist or you do not have access to it.".format(API_MODEL))
            print("\n************\n** MODEL NOT FOUND **\n************\n")
        else:
            print(f"Error calling OpenAI API for movement {movement_number}:")
            print(e)
        sys.exit(1)
    
    result_text = response.choices[0].message.content.strip()
    # Extract only the CSV-formatted block from the API output.
    csv_block = extract_csv_block(result_text)
    if PRINT_API_RESPONSE:
        print(f"\nAPI Response (CSV Block) for movement {movement_number}:\n{csv_block}\n")
    else:
        print(f"Received API response for movement {movement_number}.")
    return csv_block

def parse_api_csv(api_csv_text):
    """
    Parse the CSV text returned by the API and return a dictionary mapping
    ItemNumber (as string) to the score for the movement.
    Assumes the CSV contains at least "ItemNumber" and one additional column with numeric scores.
    """
    scores = {}
    reader = csv.DictReader(StringIO(api_csv_text))
    headers = reader.fieldnames
    if headers is None or "ItemNumber" not in headers:
        raise ValueError("API CSV output missing required header 'ItemNumber'.")
    
    # Assume the score is in the first column after "ItemNumber" (ignoring common metadata)
    score_column = None
    for h in headers:
        if h.strip() != "ItemNumber" and h.strip() not in {"Type", "PrimaryRegion", "Side", "Name", "OtherRegions"}:
            score_column = h.strip()
            break
    if score_column is None:
        raise ValueError("Could not determine which column contains the movement score.")
    
    for row in reader:
        item = row["ItemNumber"].strip()
        score_str = row.get(score_column, "").strip()
        try:
            score = float(score_str)
        except Exception:
            score = 0.0
        scores[item] = score
    return scores

def update_csv_for_movement(existing_data, movement_column, movement_scores, headers):
    """
    Update the existing CSV data (list of dictionaries) by inserting the score from movement_scores
    into the column corresponding to the movement.
    movement_scores is a dict mapping ItemNumber (string) to the score.
    """
    if movement_column not in headers:
        headers.append(movement_column)
        for row in existing_data:
            row[movement_column] = ""
    for row in existing_data:
        item = row.get("Number", "").strip()
        if item in movement_scores:
            row[movement_column] = movement_scores[item]
        else:
            row[movement_column] = ""
    return existing_data, headers

def main():
    # Load existing CSV data (the file to be updated)
    if not os.path.exists(CSV_FILENAME):
        print(f"Error: CSV file '{CSV_FILENAME}' not found at expected location: {os.path.abspath(CSV_FILENAME)}")
        sys.exit(1)
    existing_data, headers = load_csv_as_dicts(CSV_FILENAME)
    print(f"Loaded CSV file '{CSV_FILENAME}' with {len(existing_data)} rows and {len(headers)} columns.")
    
    # Load muscle data from separate MuscleList.csv
    if not os.path.exists(MUSCLE_FILENAME):
        print(f"Error: Muscle CSV file '{MUSCLE_FILENAME}' not found at expected location: {os.path.abspath(MUSCLE_FILENAME)}")
        sys.exit(1)
    muscle_data, muscle_headers = load_csv_as_dicts(MUSCLE_FILENAME)
    print(f"Loaded Muscle CSV file '{MUSCLE_FILENAME}' with {len(muscle_data)} rows and {len(muscle_headers)} columns.")
    
    # Generate muscle context from the muscle CSV (using exactly 6 columns)
    muscle_context = get_muscle_context(muscle_data)
    
    # Determine movement columns by scanning headers in the main CSV for numeric values.
    metadata_headers = {"Number", "Type", "PrimaryRegion", "Side", "Name", "OtherRegions"}
    movement_columns = [h for h in headers if h not in metadata_headers and h.strip().isdigit()]
    
    # Process movement columns in numeric order
    movement_columns = sorted(movement_columns, key=lambda x: int(x))
    if not movement_columns:
        print("No movement columns found in the CSV. Exiting.")
        sys.exit(0)
    
    print(f"Found movement columns: {movement_columns}")
    
    # Iterate over each detected movement column
    for movement in movement_columns:
        print(f"\n=== Analyzing movement number {movement} ===")
        api_output = call_openai_api_for_movement(movement, muscle_context)
        if "OUTPUT LIMIT REACHED" in api_output.upper():
            print("\n********************")
            print("** OUTPUT LIMIT REACHED **")
            print("********************\n")
            continue  # Skip updating this movement
        
        try:
            movement_scores = parse_api_csv(api_output)
        except Exception as e:
            print(f"Error parsing CSV output for movement {movement}: {e}")
            continue
        
        print(f"Updating CSV data for movement {movement}...")
        existing_data, headers = update_csv_for_movement(existing_data, movement, movement_scores, headers)
        # Write intermediate update to file
        write_csv_from_dicts(CSV_FILENAME, existing_data, headers)
        print(f"Movement {movement} updated successfully in '{CSV_FILENAME}'.")
        # Pause briefly to avoid rapid-fire API calls
        time.sleep(1)
    
    print("\nAll detected movement columns have been processed.")

if __name__ == '__main__':
    main()
