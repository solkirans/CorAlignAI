import re
import openai
import mysql.connector

# ==========================
# Configuration Parameters
# ==========================

API_CREDENTIALS = {
    "api_url": "https://api.openai.com/v1/chat/completions",
    "api_key": "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",  # Your API key
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

# Scaling factor for TINYINT conversion
SCALE_FACTOR = 127

# ==========================
# Helper Functions
# ==========================

def scale_score(score: float) -> int:
    """Convert -1..1 float to TINYINT range (-127 to 127)"""
    scaled = round(score * SCALE_FACTOR)
    return max(min(scaled, 127), -127)  # Clamp to valid range

def get_valid_muscles(cursor):
    """Retrieve all valid muscles with metadata"""
    cursor.execute("SELECT muscle_id, name, side FROM muscles")
    return [
        {"id": row[0], "name": row[1], "side": row[2]}
        for row in cursor.fetchall()
    ]

def get_yoga_moves(cursor):
    """Retrieve all yoga moves from the database"""
    cursor.execute("SELECT id, name, side, HowToDoIt FROM yogamoves")
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def build_prompt(yoga_move, muscles):
    """Create the prompt with formatted muscle list"""
    muscle_list = "\n".join(
        f"ID: {m['id']}, Name: {m['name']}, Side: {m['side']}"
        for m in muscles
    )
    
    return f"""Analyze this yoga movement:

{yoga_move['name']} ({yoga_move['side']})
{yoga_move['HowToDoIt']}

for each muscle (using the muscle IDs from the muscles table), determine the relative effect of that movement. Use a score between –1 and 1, where:

-A positive score indicates that the muscle is being stretched (i.e. lengthened).
-A negative score indicates that the muscle is being contracted or tightened.
Your analysis should be based on scientific principles—including electromyographic (EMG) studies—and should consider subtle muscle activations due to breathing and postural balance (which are especially important for patients with scoliosis). Even a simple standing posture requires low-level activation (for example, around 0.05) to maintain alignment. Adjust the scaling of other movements accordingly so that a movement requiring maximal contraction (as in heavy strength training) might score 1, whereas one that involves only gentle stretching might score between 0.05 and 0.2. 

Do not include any sample data. Make it fully scientific.
-Consider that, if a movement that focuses on one side of the body has certain level stretch or train effect, 
then the opposite side movement has the mirrored effect on the opposite side. Use this information to create better confirmation mechanism for the scores you assign.

-Additional Notes & Resources for Refinement (for your own review):

--Scientific Background & EMG Studies:
---Yoga Journal – Anatomy in Yoga Poses
---PubMed search for “EMG analysis yoga”

--Breathing & Postural Muscle Activation:
---Research on diaphragmatic breathing and postural stabilization can offer insight into low-level muscle activations in even simple poses.

Output format: [muscle_id],[score]
Example:
15,0.25
23,-0.1
42,0.05

Provide ONLY numeric CSV data.

Muscle List:
{muscle_list}

"""

def call_chatgpt(api_creds, prompt):
    """Call OpenAI API with error handling"""
    openai.api_key = api_creds["api_key"]
    try:
        response = openai.chat.completions.create(
            model=api_creds["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=float(api_creds["temperature"])
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API Error: {str(e)}")
        raise

def parse_csv_from_response(response_text):
    """Parse and scale response values"""
    pattern = re.compile(r"^\s*(\d+)\s*,\s*([-+]?\d*\.?\d+)\s*$")
    mapping = []
    
    for line in response_text.splitlines():
        line = line.strip()
        if match := pattern.match(line):
            try:
                muscle_id = int(match.group(1))
                raw_score = float(match.group(2))
                if -1 <= raw_score <= 1:
                    scaled_score = scale_score(raw_score)
                    mapping.append((muscle_id, scaled_score))
            except ValueError:
                continue
    return mapping

def insert_mapping(cursor, yoga_move_id, muscle_id, scaled_score):
    """Insert scaled TINYINT value"""
    try:
        cursor.execute("SELECT 1 FROM muscles WHERE muscle_id = %s", (muscle_id,))
        if not cursor.fetchone():
            print(f"⚠️ Invalid muscle_id {muscle_id}")
            return False

        query = """
            INSERT INTO yogamovemusclemapping 
            (yoga_move_id, muscle_id, relation_strength)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (yoga_move_id, muscle_id, scaled_score))
        return True
    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")
        return False

# ==========================
# Main Processing Logic
# ==========================

def main():
    conn = mysql.connector.connect(**DB_CREDENTIALS)
    cursor = conn.cursor()
    
    try:
        muscles = get_valid_muscles(cursor)
        if not muscles:
            raise ValueError("No muscles found in database")
            
        valid_ids = {m["id"] for m in muscles}
        yoga_moves = get_yoga_moves(cursor)
        
        for move in yoga_moves:
            move_id = move['id']
            cursor.execute("""
                SELECT COUNT(*) 
                FROM yogamovemusclemapping 
                WHERE yoga_move_id = %s
            """, (move_id,))
            if cursor.fetchone()[0] > 0:
                print(f"⏩ Skipping processed move ID {move_id}")
                continue

            try:
                prompt = build_prompt(move, muscles)
                response = call_chatgpt(API_CREDENTIALS, prompt)
                mapping = parse_csv_from_response(response)
                
                if not mapping:
                    print(f"⚠️ No valid data for move ID {move_id}")
                    continue
                
                success_count = 0
                for muscle_id, scaled_score in mapping:
                    if muscle_id not in valid_ids:
                        print(f"⚠️ Invalid muscle ID {muscle_id} in response")
                        continue
                    if insert_mapping(cursor, move_id, muscle_id, scaled_score):
                        success_count += 1
                
                if success_count > 0:
                    conn.commit()
                    print(f"✅ Processed move ID {move_id} ({success_count} mappings)")
                else:
                    print(f"⚠️ No valid inserts for move ID {move_id}")
                    
            except Exception as e:
                print(f"❌ Failed processing move ID {move_id}: {str(e)}")
                conn.rollback()

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()