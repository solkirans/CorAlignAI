import mysql.connector
from mysql.connector import Error

def create_connection():
    """
    Connect to the MySQL database 'muscledB'.
    Update the host, user, and password parameters as needed.
    """
    connection = mysql.connector.connect(
        host='localhost',         # Change if your MySQL server is hosted elsewhere
        user='root',      # Replace with your MySQL username
        password='416525',  # Replace with your MySQL password
        database='muscledB'       # Database name as specified
    )
    return connection

def create_regions_table(connection):
    """
    Create the Regions table if it does not already exist.
    The table includes:
      - region_id: auto-incrementing primary key
      - region_name: name of the region
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS Regions (
        region_id INT AUTO_INCREMENT PRIMARY KEY,
        region_name VARCHAR(255) NOT NULL
    );
    """
    cursor = connection.cursor()
    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()
    print("Regions table created or already exists.")

def insert_regions(connection):
    """
    Insert the specified region names into the Regions table.
    """
    regions = [
        "Head & TMJ",
        "Cervical",
        "Shoulder Girdle & Scapular Region",
        "Thoracic Region",
        "Abdominal & Core Region",
        "Lumbar & Lower Back Region",
        "Pelvic Girdle & Hip Region",
        "Thigh (Knee) Region",
        "Lower Leg",
        "Foot/Ankle"
    ]
    
    insert_query = "INSERT INTO Regions (region_name) VALUES (%s)"
    cursor = connection.cursor()
    
    for region in regions:
        cursor.execute(insert_query, (region,))
    
    connection.commit()
    cursor.close()
    print("Region names inserted successfully.")

def main():
    try:
        # Connect to the database
        connection = create_connection()
        print("Connected to the 'muscledB' database.")
        
        # Create the Regions table
        create_regions_table(connection)
        
        # Insert region names into the Regions table
        insert_regions(connection)
    
    except Error as e:
        print("An error occurred:", e)
    
    finally:
        if connection.is_connected():
            connection.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    main()
