import requests
import json
import re
import mysql.connector
from mysql.connector import Error

# API and Database credentials
API_CREDENTIALS = {
    "api_url": "https://api.openai.com/v1/chat/completions",
    "api_key": "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",
    "model": "o3-mini-2025-01-31",
    "temperature": 1
}

DB_CREDENTIALS = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "416525",
    "database": "muscledB"
}

def try_fix_json(text):
    """
    Attempt to load JSON from text.
    If direct parsing fails, try replacing single quotes with double quotes.
    Returns a Python object (dict) or None if unable to parse.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Attempt to fix by replacing single quotes with double quotes
        fixed_text = text.replace("'", '"')
        try:
            return json.loads(fixed_text)
        except Exception as e2:
            print("Failed to fix JSON:", e2)
            return None

def get_all_muscles(cursor):
    """
    Retrieve all muscle records from the muscles table.
    Returns a list of dictionaries.
    """
    cursor.execute("SELECT muscle_id, type, side, name, primary_region, other_regions FROM muscles")
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    muscles = [dict(zip(columns, row)) for row in rows]
    return muscles

def get_all_questions(cursor):
    """
    Retrieve all question records from the questions table.
    Returns a list of dictionaries.
    """
    cursor.execute("SELECT question_id, question_text, questions_type FROM questions")
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    questions = [dict(zip(columns, row)) for row in rows]
    return questions

def get_muscle_matrix(question_text, muscles_data):
    """
    Call the OpenAI API to generate the muscle assessment matrix for a given question.
    The prompt includes the full muscles data (as JSON) and the question text.
    Expected response is a JSON object mapping muscle identifiers to a value between -100 and 100.
    """
    muscles_json = json.dumps(muscles_data)
    prompt = (
        "Create the Muscle Assessment Matrix by using scientific resources as a reference. "
        "Use larger values if the relation between that question and that muscle is stronger. "
        "Muscle Assessment Matrix values should be between -100 and 100. Consider the chain effect on posture. "
        "Consider compensating behavior of posture problems. Consider that the main focus area of the question can affect neighboring areas; "
        "for example, a weak muscle in the foot can create compensating tightness in the thoracic region.  "
        "Use biomechanical bilateral equations, clinical information, or scientific data to fill the matrix. "
        "If you cannot find solid information, use approximated or predicted values but try to make those predictions as accurate as possible. "
        "Verify your data by checking the symmetry of values.\n\n"
        "Muscles (full data):\n" + muscles_json + "\n\n"
        "Question: " + question_text + "\n\n"
        "Return the result as a JSON object mapping each muscle's identifier (as a number) to a value (integer) between -100 and 100."
    )
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_CREDENTIALS['api_key']}"
    }
    
    data = {
        "model": API_CREDENTIALS["model"],
        "messages": [
            {"role": "system", "content": "You are a biomechanical and clinical expert."},
            {"role": "user", "content": prompt}
        ],
        "temperature": API_CREDENTIALS["temperature"]
    }
    
    response = requests.post(API_CREDENTIALS["api_url"], headers=headers, json=data)
    if response.status_code == 200:
        try:
            resp_json = response.json()
            content = resp_json["choices"][0]["message"]["content"]
            content = content.strip()
            # Remove markdown code block markers if present.
            if content.startswith("```") and content.endswith("```"):
                lines = content.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines).strip()
            # Try to load JSON.
            matrix_mapping = try_fix_json(content)
            if matrix_mapping is None:
                print("Failed to parse matrix mapping JSON.")
                return {}
            return matrix_mapping
        except Exception as e:
            print("Error parsing API response:", e)
            return {}
    else:
        print("API request failed:", response.status_code, response.text)
        return {}

def insert_matrix_value(cursor, question_id, muscle_id, relation_value):
    """
    Insert a muscle relation value for a question into the muscle_assessment_matrix table.
    Assumes table structure: (id AUTO_INCREMENT, question_id, muscle_id, relation_value).
    """
    sql = """
    INSERT INTO muscle_assessment_matrix (question_id, muscle_id, relation_value)
    VALUES (%s, %s, %s)
    """
    cursor.execute(sql, (question_id, muscle_id, relation_value))

def main():
    try:
        connection = mysql.connector.connect(
            host=DB_CREDENTIALS["host"],
            port=DB_CREDENTIALS["port"],
            user=DB_CREDENTIALS["user"],
            password=DB_CREDENTIALS["password"],
            database=DB_CREDENTIALS["database"]
        )
        if connection.is_connected():
            print("Connected to the database.")
            cursor = connection.cursor(dictionary=True)
            
            # Retrieve muscles and questions from the database.
            muscles_data = get_all_muscles(cursor)
            questions = get_all_questions(cursor)
            
            for question in questions:
                q_id = question["question_id"]
                q_text = question["question_text"]
                print(f"Processing muscle matrix for Question ID {q_id}: {q_text}")
                
                matrix_mapping = get_muscle_matrix(q_text, muscles_data)
                if not matrix_mapping:
                    print(f"No matrix returned for question ID {q_id}; skipping.")
                    continue
                
                # Insert each muscle relation into the muscle_assessment_matrix table.
                for muscle_key, relation_value in matrix_mapping.items():
                    try:
                        # Attempt to extract a numeric muscle ID from the key.
                        match = re.search(r'(\d+)', muscle_key)
                        if match:
                            muscle_id = int(match.group(1))
                        else:
                            # If no numeric part is found, skip this key.
                            print(f"Warning: Cannot extract numeric muscle id from key: {muscle_key}. Skipping this key.")
                            continue
                        relation_val = int(relation_value)
                        insert_matrix_value(cursor, q_id, muscle_id, relation_val)
                    except Exception as e:
                        print(f"Error inserting matrix value for muscle '{muscle_key}' for question ID {q_id}: {e}")
                connection.commit()
                print(f"Inserted muscle matrix values for Question ID {q_id}.")
            
            cursor.close()
            connection.close()
            print("Database connection closed.")
    except Error as e:
        print("Error while connecting to MySQL:", e)

if __name__ == "__main__":
    main()
