import requests
import json
import re
import mysql.connector
from mysql.connector import Error

# API credentials and DB credentials
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

# Mapping of question category to region_id based on your Regions Table
region_mapping = {
    'tmj_jaw': 1, 
    'head': 1, 
    'neck': 2, 
    'shoulders': 3, 
    'chest_ribcage': 4, 
    'thoracic_spine': 4, 
    'lumbar_spine': 6, 
    'core': 5, 
    'pelvis_si': 7, 
    'hips': 7, 
    'knees': 8, 
    'ankles_feet': 10, 
    'weight_distribution': 10, 
    'dynamic_assessment': None, 
    'pain_assessment': None
}

# QUESTIONS dictionary with your provided questions
QUESTIONS = {
    'tmj_jaw': [
        ('l_tmj_tension', 'Left TMJ tension? (0=normal, 10=severe)'),
        ('r_tmj_tension', 'Right TMJ tension? (0=normal, 10=severe)'),
        ('l_jaw_position', 'Left jaw position? (-10=retracted, 0=neutral, 10=protruded)'),
        ('r_jaw_position', 'Right jaw position? (-10=retracted, 0=neutral, 10=protruded)')
    ],
    'head': [
        ('l_head_weight', 'Left side head weight? (-10=light, 0=balanced, 10=heavy)'),
        ('r_head_weight', 'Right side head weight? (-10=light, 0=balanced, 10=heavy)'),
        ('head_tilt_sagittal', 'Head tilt forward/back? (-10=down, 0=neutral, 10=up)'),
        ('l_ear_shoulder', 'Left ear-shoulder alignment? (-10=forward, 0=aligned, 10=behind)'),
        ('r_ear_shoulder', 'Right ear-shoulder alignment? (-10=forward, 0=aligned, 10=behind)')
    ],
    'neck': [
        ('l_neck_tilt', 'Left side neck compression? (-10=compressed, 0=neutral, 10=stretched)'),
        ('r_neck_tilt', 'Right side neck compression? (-10=compressed, 0=neutral, 10=stretched)'),
        ('l_neck_rotation', 'Left neck rotation range? (-10=limited, 0=normal, 10=excessive)'),
        ('r_neck_rotation', 'Right neck rotation range? (-10=limited, 0=normal, 10=excessive)'),
        ('neck_forward', 'Forward head position? (0=normal, 10=severe)')
    ],
    'shoulders': [
        ('l_shoulder_height', 'Left shoulder height? (0=normal, 10=elevated)'),
        ('r_shoulder_height', 'Right shoulder height? (0=normal, 10=elevated)'),
        ('l_shoulder_forward', 'Left shoulder rounding? (0=normal, 10=severe)'),
        ('r_shoulder_forward', 'Right shoulder rounding? (0=normal, 10=severe)'),
        ('l_scapula_position', 'Left shoulder blade position? (-10=wings out, 0=normal, 10=tucked in)'),
        ('r_scapula_position', 'Right shoulder blade position? (-10=wings out, 0=normal, 10=tucked in)'),
        ('l_scapula_winging', 'Left shoulder blade winging during movement? (0=none, 10=severe)'),
        ('r_scapula_winging', 'Right shoulder blade winging during movement? (0=none, 10=severe)')
    ],
    'chest_ribcage': [
        ('l_pec_tension', 'Left chest muscle tension? (0=normal, 10=tight)'),
        ('r_pec_tension', 'Right chest muscle tension? (0=normal, 10=tight)'),
        ('l_ribcage_position', 'Left ribcage position? (-10=depressed, 0=neutral, 10=elevated)'),
        ('r_ribcage_position', 'Right ribcage position? (-10=depressed, 0=neutral, 10=elevated)'),
        ('l_breathing_pattern', 'Left side breathing movement? (0=minimal, 5=normal, 10=excessive)'),
        ('r_breathing_pattern', 'Right side breathing movement? (0=minimal, 5=normal, 10=excessive)')
    ],
    'thoracic_spine': [
        ('l_thoracic_rotation', 'Left thoracic rotation range? (-10=limited, 0=normal, 10=excessive)'),
        ('r_thoracic_rotation', 'Right thoracic rotation range? (-10=limited, 0=normal, 10=excessive)'),
        ('l_thoracic_tension', 'Left upper back tension? (0=none, 10=severe)'),
        ('r_thoracic_tension', 'Right upper back tension? (0=none, 10=severe)'),
        ('l_thoracic_flexibility', 'Left upper back flexibility? (0=normal, 10=stiff)'),
        ('r_thoracic_flexibility', 'Right upper back flexibility? (0=normal, 10=stiff)'),
        ('thoracic_curve', 'Overall upper back curve? (0=normal, 10=excessive rounding)')
    ],
    'lumbar_spine': [
        ('l_lumbar_tension', 'Left lower back tension? (0=none, 10=severe)'),
        ('r_lumbar_tension', 'Right lower back tension? (0=none, 10=severe)'),
        ('l_lumbar_rotation', 'Left lower back rotation? (-10=limited, 0=normal, 10=excessive)'),
        ('r_lumbar_rotation', 'Right lower back rotation? (-10=limited, 0=normal, 10=excessive)'),
        ('l_lumbar_sidebend', 'Left lower back side bend? (-10=limited, 0=normal, 10=excessive)'),
        ('r_lumbar_sidebend', 'Right lower back side bend? (-10=limited, 0=normal, 10=excessive)'),
        ('lumbar_curve', 'Overall lower back curve? (-10=flat, 0=normal, 10=excessive)')
    ],
    'core': [
        ('l_upper_abs', 'Left upper abdominal tone? (0=weak, 5=normal, 10=excessive)'),
        ('r_upper_abs', 'Right upper abdominal tone? (0=weak, 5=normal, 10=excessive)'),
        ('l_lower_abs', 'Left lower abdominal tone? (0=weak, 5=normal, 10=excessive)'),
        ('r_lower_abs', 'Right lower abdominal tone? (0=weak, 5=normal, 10=excessive)'),
        ('l_obliques', 'Left oblique strength? (0=weak, 5=normal, 10=excessive)'),
        ('r_obliques', 'Right oblique strength? (0=weak, 5=normal, 10=excessive)')
    ],
    'pelvis_si': [
        ('l_si_joint', 'Left SI joint position? (-10=posterior, 0=neutral, 10=anterior)'),
        ('r_si_joint', 'Right SI joint position? (-10=posterior, 0=neutral, 10=anterior)'),
        ('l_psis_height', 'Left PSIS height? (-10=low, 0=level, 10=high)'),
        ('r_psis_height', 'Right PSIS height? (-10=low, 0=level, 10=high)'),
        ('l_asis_height', 'Left ASIS height? (-10=low, 0=level, 10=high)'),
        ('r_asis_height', 'Right ASIS height? (-10=low, 0=level, 10=high)')
    ],
    'hips': [
        ('l_hip_rotation', 'Left hip rotation? (-10=internal, 0=neutral, 10=external)'),
        ('r_hip_rotation', 'Right hip rotation? (-10=internal, 0=neutral, 10=external)'),
        ('l_hip_height', 'Left hip height? (-10=low, 0=level, 10=high)'),
        ('r_hip_height', 'Right hip height? (-10=low, 0=level, 10=high)'),
        ('l_hip_shift', 'Left hip shift? (-10=back, 0=centered, 10=forward)'),
        ('r_hip_shift', 'Right hip shift? (-10=back, 0=centered, 10=forward)'),
        ('l_glute_tone', 'Left gluteal tone? (0=weak, 5=normal, 10=excessive)'),
        ('r_glute_tone', 'Right gluteal tone? (0=weak, 5=normal, 10=excessive)'),
        ('l_hip_flexor', 'Left hip flexor tension? (0=normal, 10=tight)'),
        ('r_hip_flexor', 'Right hip flexor tension? (0=normal, 10=tight)')
    ],
    'knees': [
        ('l_knee_alignment', 'Left knee alignment? (-10=knock knee, 0=straight, 10=bow legged)'),
        ('r_knee_alignment', 'Right knee alignment? (-10=knock knee, 0=straight, 10=bow legged)'),
        ('l_knee_rotation', 'Left knee rotation? (-10=internal, 0=straight, 10=external)'),
        ('r_knee_rotation', 'Right knee rotation? (-10=internal, 0=straight, 10=external)'),
        ('l_patella_tracking', 'Left kneecap tracking? (-10=medial, 0=central, 10=lateral)'),
        ('r_patella_tracking', 'Right kneecap tracking? (-10=medial, 0=central, 10=lateral)'),
        ('l_knee_hyperext', 'Left knee hyperextension? (0=none, 10=severe)'),
        ('r_knee_hyperext', 'Right knee hyperextension? (0=none, 10=severe)'),
        ('l_q_angle', 'Left Q-angle? (-10=decreased, 0=normal, 10=increased)'),
        ('r_q_angle', 'Right Q-angle? (-10=decreased, 0=normal, 10=increased)')
    ],
    'ankles_feet': [
        ('l_ankle_position', 'Left ankle position? (-10=varus, 0=neutral, 10=valgus)'),
        ('r_ankle_position', 'Right ankle position? (-10=varus, 0=neutral, 10=valgus)'),
        ('l_arch_height', 'Left arch height? (-10=flat, 0=normal, 10=high)'),
        ('r_arch_height', 'Right arch height? (-10=flat, 0=normal, 10=high)'),
        ('l_foot_rotation', 'Left foot rotation? (-10=inward, 0=straight, 10=outward)'),
        ('r_foot_rotation', 'Right foot rotation? (-10=inward, 0=straight, 10=outward)'),
        ('l_toe_position', 'Left toe position? (-10=hammer toes, 0=normal, 10=bunion)'),
        ('r_toe_position', 'Right toe position? (-10=hammer toes, 0=normal, 10=bunion)')
    ],
    'weight_distribution': [
        ('l_heel_pressure', 'Left heel pressure? (0=minimal, 5=normal, 10=excessive)'),
        ('r_heel_pressure', 'Right heel pressure? (0=minimal, 5=normal, 10=excessive)'),
        ('l_forefoot_pressure', 'Left forefoot pressure? (0=minimal, 5=normal, 10=excessive)'),
        ('r_forefoot_pressure', 'Right forefoot pressure? (0=minimal, 5=normal, 10=excessive)'),
        ('l_lateral_pressure', 'Left outer foot pressure? (0=minimal, 5=normal, 10=excessive)'),
        ('r_lateral_pressure', 'Right outer foot pressure? (0=minimal, 5=normal, 10=excessive)'),
        ('l_medial_pressure', 'Left inner foot pressure? (0=minimal, 5=normal, 10=excessive)'),
        ('r_medial_pressure', 'Right inner foot pressure? (0=minimal, 5=normal, 10=excessive)')
    ],
    'dynamic_assessment': [
        ('l_single_leg', 'Left single leg stability? (0=stable, 10=unstable)'),
        ('r_single_leg', 'Right single leg stability? (0=stable, 10=unstable)'),
        ('l_weight_shift', 'Left side weight shift control? (0=controlled, 10=uncontrolled)'),
        ('r_weight_shift', 'Right side weight shift control? (0=controlled, 10=uncontrolled)'),
        ('l_arm_raising', 'Left arm raising pattern? (0=smooth, 10=compensated)'),
        ('r_arm_raising', 'Right arm raising pattern? (0=smooth, 10=compensated)'),
        ('squat_symmetry', 'Squat pattern symmetry? (-10=left dominated, 0=balanced, 10=right dominated)'),
        ('gait_symmetry', 'Walking pattern symmetry? (-10=left dominated, 0=balanced, 10=right dominated)')
    ],
    'pain_assessment': [
        ('l_upper_pain', 'Left upper body pain? (0=none, 10=severe)'),
        ('r_upper_pain', 'Right upper body pain? (0=none, 10=severe)'),
        ('l_lower_pain', 'Left lower body pain? (0=none, 10=severe)'),
        ('r_lower_pain', 'Right lower body pain? (0=none, 10=severe)')
    ]
}

def parse_score_range(text):
    """
    Parse the score range from the question text.
    For example, given 'Left TMJ tension? (0=normal, 10=severe)'
    it returns (0, 10) or for '(-10=retracted, 0=neutral, 10=protruded)', it returns (-10, 10)
    """
    pattern = r'\(([^)]*)\)'
    match = re.search(pattern, text)
    if match:
        content = match.group(1)
        numbers = re.findall(r'(-?\d+)', content)
        if numbers:
            try:
                nums = list(map(int, numbers))
                return min(nums), max(nums)
            except Exception as e:
                print("Error converting numbers:", e)
                return None, None
    return None, None

def get_detailed_question(original_question):
    """
    Calls the ChatGPT API to generate a more understandable and detailed version of the question.
    Returns a dictionary with keys 'question_text' and 'assessment'.
    """
    prompt = (
        "I need to add more details for the question part. Make it something an average person can understand.\n"
        "Use the question below to generate detailed assessment descriptions and a better structured question text.\n"
        "Return your answer in JSON format with two keys: 'question_text' for the improved question and 'assessment' for the detailed description of how to do the assesment. Questions anddetailed assesment must use *you* language, because questions will be answered by patient\n"
        f"Question: {original_question}"
    )
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_CREDENTIALS['api_key']}"
    }
    
    data = {
        "model": API_CREDENTIALS["model"],
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": API_CREDENTIALS["temperature"]
    }
    
    response = requests.post(API_CREDENTIALS["api_url"], headers=headers, json=data)
    if response.status_code == 200:
        try:
            response_json = response.json()
            content = response_json["choices"][0]["message"]["content"]
            result = json.loads(content)
            return result
        except Exception as e:
            print("Error parsing API response:", e)
            return {"question_text": original_question, "assessment": ""}
    else:
        print("API request failed:", response.status_code, response.text)
        return {"question_text": original_question, "assessment": ""}

def insert_question_into_db(cursor, question_text, questions_type, assessment, region_id, score_min, score_max):
    """
    Inserts a question record into the 'questions' table.
    """
    sql = """
    INSERT INTO questions (question_text, questions_type, assessment, region_id, ScoreMin, ScoreMax)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (question_text, questions_type, assessment, region_id, score_min, score_max))

def main():
    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(
            host=DB_CREDENTIALS["host"],
            port=DB_CREDENTIALS["port"],
            user=DB_CREDENTIALS["user"],
            password=DB_CREDENTIALS["password"],
            database=DB_CREDENTIALS["database"]
        )
        if connection.is_connected():
            print("Connected to the database.")
            cursor = connection.cursor()
            
            # Loop through each category and question
            for category, questions_list in QUESTIONS.items():
                for q_id, original_question in questions_list:
                    print(f"Processing question: {original_question}")
                    
                    # Get the refined question details from the API
                    detailed = get_detailed_question(original_question)
                    refined_question_text = detailed.get("question_text", original_question)
                    assessment_text = detailed.get("assessment", "")
                    
                    # Parse the scoring range from the original question text
                    score_min, score_max = parse_score_range(original_question)
                    
                    # Get the appropriate region_id from the mapping (if available)
                    region_id = region_mapping.get(category, None)
                    
                    # Insert the record into the database
                    insert_question_into_db(cursor, refined_question_text, category, assessment_text, region_id, score_min, score_max)
                    connection.commit()
                    print("Inserted question into the database.")
            
            cursor.close()
            connection.close()
            print("Database connection closed.")
            
    except Error as e:
        print("Error while connecting to MySQL:", e)

if __name__ == "__main__":
    main()
