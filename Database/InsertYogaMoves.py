import csv
import mysql.connector
from mysql.connector import Error

def create_connection():
    """
    Connect to the MySQL database.
    Update the host, user, password, and database parameters as needed.
    """
    connection = mysql.connector.connect(
        host='localhost',         # Update if your MySQL server is hosted elsewhere
        user='root',      # Replace with your MySQL username
        password='416525',  # Replace with your MySQL password
        database='muscledB'   # Replace with your target database name
    )
    return connection

def create_yogamoves_table(connection):
    """
    Create the YogaMoves table if it does not already exist.
    The table includes:
      - ID: Primary key (from the CSV's Number field), INT AUTO_INCREMENT.
      - Name, Side, HowToDoIt, AlignmentCues, PrimaryFocusAreas, WhatToFeel,
        VariationsForDifferentCurvatures, Adaptations, OutcomeBenefits,
        FeedbackIndicators.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS YogaMoves (
        ID INT AUTO_INCREMENT PRIMARY KEY,
        Name VARCHAR(255),
        Side VARCHAR(50),
        HowToDoIt TEXT,
        AlignmentCues TEXT,
        PrimaryFocusAreas TEXT,
        WhatToFeel TEXT,
        VariationsForDifferentCurvatures TEXT,
        Adaptations TEXT,
        OutcomeBenefits TEXT,
        FeedbackIndicators TEXT
    );
    """
    cursor = connection.cursor()
    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()
    print("YogaMoves table created (if it did not exist).")

def insert_yogamoves_from_csv(connection, filename):
    """
    Read the CSV file and insert each row into the YogaMoves table.
    The CSV file is expected to have the following header row:
    Number,Name,Side,How to Do It,Alignment Cues,Primary Focus Areas,What to Feel,
    Variations for Different Curvatures,Adaptations,Outcome & Benefits,Feedback Indicators
    """
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO YogaMoves (ID, Name, Side, HowToDoIt, AlignmentCues, PrimaryFocusAreas, WhatToFeel, VariationsForDifferentCurvatures, Adaptations, OutcomeBenefits, FeedbackIndicators)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                # Extract and convert the values from the CSV row.
                id_value = int(row['Number'])
                name = row['Name']
                side = row['Side']
                how_to_do_it = row['How to Do It']
                alignment_cues = row['Alignment Cues']
                primary_focus_areas = row['Primary Focus Areas']
                what_to_feel = row['What to Feel']
                variations = row['Variations for Different Curvatures']
                adaptations = row['Adaptations']
                outcome_benefits = row['Outcome & Benefits']
                feedback_indicators = row['Feedback Indicators']

                data = (id_value, name, side, how_to_do_it, alignment_cues, primary_focus_areas,
                        what_to_feel, variations, adaptations, outcome_benefits, feedback_indicators)
                cursor.execute(insert_query, data)
            except Exception as e:
                print("Error processing row:", row)
                print(e)
    
    connection.commit()
    cursor.close()
    print("Data inserted into YogaMoves table from", filename)

def main():
    try:
        connection = create_connection()
        print("Connected to the database.")
        
        create_yogamoves_table(connection)
        insert_yogamoves_from_csv(connection, 'YogaDescriptionList.csv')
        
    except Error as e:
        print("Error:", e)
    
    finally:
        if connection.is_connected():
            connection.close()
            print("Connection closed.")

if __name__ == "__main__":
    main()
