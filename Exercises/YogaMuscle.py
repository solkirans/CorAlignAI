import re
import requests
import mysql.connector

def load_api_credentials(filename):
    """
    Reads API credentials and payload parameters from keyAPI.txt.
    Expected format (each on a separate line):
      api_url=https://api.example.com/o3mini
      api_key=YOUR_API_KEY_HERE
      model=o3-mini
      max_tokens=1500
      temperature=0.0
    """
    creds = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                creds[key.strip()] = value.strip()
    required_keys = ["api_url", "api_key", "model", "max_tokens", "temperature"]
    for key in required_keys:
        if key not in creds:
            raise ValueError(f"Missing {key} in API credentials file.")
    return creds

def load_db_credentials(filename):
    """
    Reads DB credentials from keyDB.txt.
    Expected format (each on a separate line):
      host=localhost
      port=3306
      user=root
      password=YOUR_DB_PASSWORD
      database=muscledB
    """
    creds = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                creds[key.strip()] = value.strip()
    if 'port' in creds:
        creds['port'] = int(creds['port'])
    required = ['host', 'port', 'user', 'password', 'database']
    for key in required:
        if key not in creds:
            raise ValueError(f"Missing {key} in DB credentials file.")
    return creds

def get_yoga_moves(cursor):
    """
    Retrieves all yoga moves from the 'yogamoves' table.
    Assumes columns: id, name, side, description.
    """
    query = "SELECT id, name, side, description FROM yogamoves"
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    moves = []
    for row in cursor.fetchall():
        move = dict(zip(columns, row))
        moves.append(move)
    return moves

def build_prompt(yoga_move):
    """
    Creates the prompt for a given yoga move.
    Replaces NAME_FIELD_HERE, SIDE_FIELD_HERE, and HOW_TO_DO_IT_FIELD_HERE with actual values.
    """
    prompt = f"""I want you to analyze below yoga movement;

{yoga_move['name']}
{yoga_move['side']}
{yoga_move['description']}

for each muscle (using the muscle IDs from the muscles table), determine the relative effect of that movement. Use a score between –1 and 1, where:

-A positive score indicates that the muscle is being stretched (i.e. lengthened).
-A negative score indicates that the muscle is being contracted or tightened.
Your analysis should be based on scientific principles—including electromyographic (EMG) studies—and should consider subtle muscle activations due to breathing and postural balance (which are especially important for patients with scoliosis). Even a simple standing posture requires low-level activation (for example, around 0.05) to maintain alignment. Adjust the scaling of other movements accordingly so that a movement requiring maximal contraction (as in heavy strength training) might score 1, whereas one that involves only gentle stretching might score between 0.05 and 0.2. 

Do not include any sample data. Make it fully scientific.

-Additional Notes & Resources for Refinement (for your own review):

--Scientific Background & EMG Studies:
---Yoga Journal – Anatomy in Yoga Poses
---PubMed search for “EMG analysis yoga”

--Breathing & Postural Muscle Activation:
---Research on diaphragmatic breathing and postural stabilization can offer insight into low-level muscle activations in even simple poses.

Give output only id's of muscles and scores for corresponding yoga movement. Do not add any extra data. Use CSV format.
"""
    return prompt

def call_chatgpt(api_creds, prompt):
    """
    Sends the prompt to the ChatGPT o3 mini model.
    The API credentials and payload parameters are provided in api_creds.
    """
    headers = {
        "Authorization": f"Bearer {api_creds['api_key']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": api_creds["model"],
        "prompt": prompt,
        "max_tokens": int(api_creds["max_tokens"]),
        "temperature": float(api_creds["temperature"])
    }
    response = requests.post(api_creds["api_url"], json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    if "answer" in data:
        return data["answer"]
    else:
        raise ValueError("No 'answer' key in API response.")

def parse_csv_from_response(response_text):
    """
    Extracts muscle activation CSV data from the response text.
    Expects rows with two comma-separated values: muscle_id, score.
    Filters out any extra text.
    """
    pattern = re.compile(r"^\s*(\d+)\s*,\s*([-+]?\d*\.?\d+)\s*$")
    mapping = []
    for line in response_text.splitlines():
        line = line.strip()
        # Skip header lines if present (e.g., "id,score" or "muscle_id,score")
        if re.match(r"^(id|muscle_id)\s*,\s*(score)$", line, re.IGNORECASE):
            continue
        match = pattern.match(line)
        if match:
            muscle_id = int(match.group(1))
            score = float(match.group(2))
            mapping.append((muscle_id, score))
    return mapping

def insert_mapping(cursor, yoga_move_id, muscle_id, score):
    """
    Inserts a row into the yogamovemusclemapping table.
    Assumes columns: yoga_move_id, muscle_id, score.
    """
    query = """
        INSERT INTO yogamovemusclemapping (yoga_move_id, muscle_id, score)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (yoga_move_id, muscle_id, score))

def main():
    # Load API credentials and parameters from keyAPI.txt
    api_creds = load_api_credentials("keyAPI.txt")
    
    # Load database credentials
    db_creds = load_db_credentials("keyDB.txt")
    
    # Connect to the database (using mysql.connector)
    conn = mysql.connector.connect(
        host=db_creds["host"],
        port=db_creds["port"],
        user=db_creds["user"],
        password=db_creds["password"],
        database=db_creds["database"]
    )
    cursor = conn.cursor()
    
    try:
        # Retrieve all yoga moves from the database
        yoga_moves = get_yoga_moves(cursor)
        for move in yoga_moves:
            prompt = build_prompt(move)
            try:
                response_text = call_chatgpt(api_creds, prompt)
            except Exception as e:
                print(f"Error calling API for yoga move id {move['id']}: {e}")
                continue

            # Parse the CSV portion from the API answer
            mapping = parse_csv_from_response(response_text)
            if not mapping:
                print(f"No valid CSV mapping found for yoga move id {move['id']}.")
                continue

            # Insert each muscle mapping into the database
            for muscle_id, score in mapping:
                try:
                    insert_mapping(cursor, move['id'], muscle_id, score)
                except Exception as e:
                    print(f"Error inserting mapping for yoga move id {move['id']}, muscle {muscle_id}: {e}")
        conn.commit()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
