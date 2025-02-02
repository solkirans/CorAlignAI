import csv
import os
import sys
from io import StringIO

def load_csv_as_dicts(filename):
    """Load the CSV file as a list of dictionaries with stripped header keys."""
    data = []
    with open(filename, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        headers = [h.strip() for h in reader.fieldnames if h is not None]
        for row in reader:
            new_row = {key.strip(): (value.strip() if isinstance(value, str) else value)
                       for key, value in row.items() if key is not None}
            data.append(new_row)
    return data, headers

def transpose_csv_data(pasted_data):
    """
    Transpose pasted CSV data that is in column-wise (transposed) format.
    The CSV is expected to have a "Field" column and subsequent columns for each record.
    Returns a list of dictionaries in the normal row-wise format.
    """
    # Get the list of keys from the first row.
    keys_list = list(pasted_data[0].keys())
    if "Field" not in keys_list:
        raise ValueError("Transposed CSV expected a 'Field' column in the header.")
    # The record IDs are all keys except "Field"
    record_ids = [key for key in keys_list if key != "Field"]
    records = []
    # For each record id, create a dictionary where each field's value is taken from each row.
    for rid in record_ids:
        new_row = {}
        for row in pasted_data:
            field_name = row["Field"].strip()
            # Use empty string if key is missing
            new_row[field_name] = row.get(rid, "").strip()
        records.append(new_row)
    return records

def load_pasted_csv(pasted_text):
    """Load pasted CSV text into a list of dictionaries with stripped keys.
       If required keys are missing, assume the CSV is transposed and try to convert it.
    """
    reader = csv.DictReader(StringIO(pasted_text))
    headers = [h.strip() for h in reader.fieldnames if h is not None]
    pasted_data = []
    for row in reader:
        new_row = {key.strip(): (value.strip() if isinstance(value, str) else value)
                   for key, value in row.items() if key is not None}
        pasted_data.append(new_row)
    
    # Check if the required keys are present in the first row.
    required_keys = {"Number", "Name", "Side"}
    if not required_keys.issubset(set(pasted_data[0].keys())):
        # Assume transposed format and attempt to transpose.
        try:
            pasted_data = transpose_csv_data(pasted_data)
        except Exception as e:
            raise ValueError("Error transposing pasted CSV data: " + str(e))
    
    return pasted_data

def update_existing_rows(existing_data, existing_headers, pasted_data):
    """
    For each row in the pasted data, find a matching row (by 'Number', 'Name', and 'Side')
    in the existing_data. If found, update each cell using the pasted row's value.
    If a column in the pasted row is not in existing_headers or a matching row isn't found,
    raise an error.
    """
    existing_headers = [h.strip() for h in existing_headers]
    
    for pasted_row in pasted_data:
        for key in ["Number", "Name", "Side"]:
            if key not in pasted_row or pasted_row[key] == "":
                raise ValueError(f"Pasted data is missing required field '{key}'.")
        
        match_found = False
        for existing_row in existing_data:
            if (existing_row.get("Number", "").strip() == pasted_row.get("Number", "").strip() and 
                existing_row.get("Name", "").strip() == pasted_row.get("Name", "").strip() and 
                existing_row.get("Side", "").strip() == pasted_row.get("Side", "").strip()):
                # Update each cell for matching keys (cell-by-cell update)
                for key, value in pasted_row.items():
                    key_stripped = key.strip()
                    if key_stripped not in existing_headers:
                        raise ValueError(f"Column '{key_stripped}' not found in the existing CSV file headers.")
                    existing_row[key_stripped] = value
                match_found = True
                break
        if not match_found:
            raise ValueError(f"Matching row not found for Number: {pasted_row.get('Number')}, "
                             f"Name: {pasted_row.get('Name')}, Side: {pasted_row.get('Side')}.")
    return existing_data

def write_csv_from_dicts(filename, data, headers):
    """Write the list of dictionaries back to the CSV file using the given headers."""
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def main():
    filename = "YogaMuscleListInverted.csv"
    abs_path = os.path.abspath(filename)
    if os.path.exists(filename):
        print(f"Found existing CSV file at: {abs_path}")
    else:
        print(f"Error: CSV file not found at expected location: {abs_path}")
        sys.exit(1)
    
    while True:
        existing_data, existing_headers = load_csv_as_dicts(filename)
        
        print("\nPaste CSV update (including header) for a movement (press Enter on an empty line to finish):")
        csv_lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            csv_lines.append(line)
        
        if not csv_lines:
            print("No CSV data entered.")
        else:
            csv_text = "\n".join(csv_lines)
            try:
                pasted_data = load_pasted_csv(csv_text)
                updated_data = update_existing_rows(existing_data, existing_headers, pasted_data)
            except ValueError as e:
                print("Error during update:", e)
                continue
            write_csv_from_dicts(filename, updated_data, existing_headers)
            print(f"Data successfully updated in {filename}.")
        
        print("\nDo you want to update more CSV data? (Y/N)")
        answer = input().strip().lower()
        if answer in ["n", "no"]:
            print("Exiting program.")
            break

if __name__ == '__main__':
    main()
