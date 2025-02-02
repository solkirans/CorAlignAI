import mysql.connector
from mysql.connector import errorcode

def create_database(cursor, database_name):
    """
    Create a new database with the specified name.
    The DEFAULT CHARACTER SET is set to UTF-8.
    """
    try:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {database_name} DEFAULT CHARACTER SET 'utf8'"
        )
        print(f"Database '{database_name}' created successfully (or already exists).")
    except mysql.connector.Error as err:
        print(f"Failed creating database '{database_name}': {err}")
        exit(1)

def main():
    # Connection configuration (update with your credentials)
    config = {
        "user": "root",      # e.g., "root"
        "password": "416525",  # your MySQL password
        "host": "127.0.0.1",         # or "localhost"
        # Notice that we are not specifying the 'database' here,
        # because we want to connect to the server to create one.
    }

    try:
        # Connect to the MySQL server
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        print("Connected to MySQL server.")

        # Specify the name of the new database
        database_name = "MuscleDatabase"  # Change this to your preferred database name

        # Create the database
        create_database(cursor, database_name)

        # Optionally, you can switch to the new database:
        cursor.execute(f"USE {database_name}")
        print(f"Switched to database '{database_name}'.")

        # Cleanup
        cursor.close()
        connection.close()
        print("MySQL connection closed.")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Access denied: Check your username or password.")
        else:
            print(err)

if __name__ == "__main__":
    main()
