import mysql.connector
from mysql.connector import Error

def create_games_table(host_name, db_name, user_name, user_password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            database=db_name,
            user=user_name,
            password=user_password
        )
        cursor = connection.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS games (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title TEXT NOT NULL,
            igdb_id INT,
            cover TEXT,
            release_date TEXT,
            platforms JSON,
            genres JSON,
            rating INT,
            summary TEXT,
            metadata JSON,
            developer TEXT,
            publisher TEXT,
            tags JSON
        )
        """
        cursor.execute(create_table_query)
        print("Games table created successfully")
    except Error as e:
        print(f"Error: '{e}'")
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()
            # print("MySQL connection is closed") # Keep connection open if called sequentially

def create_local_games_table(host_name, db_name, user_name, user_password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            database=db_name,
            user=user_name,
            password=user_password
        )
        cursor = connection.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS local_games (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title TEXT NOT NULL,
            igdb_id INT UNIQUE, -- Make igdb_id unique for easier updates
            cover TEXT,
            release_date TEXT,
            platforms JSON,
            genres JSON,
            rating INT,
            summary TEXT,
            metadata JSON,
            developer TEXT,
            publisher TEXT,
            tags JSON,
            weighted_rating FLOAT -- Added weighted rating
        )
        """
        cursor.execute(create_table_query)
        print("Local_games table created successfully")
    except Error as e:
        print(f"Error creating local_games table: '{e}'")
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()
            # print("MySQL connection for local_games is closed") # Keep connection open if called sequentially

def create_users_table(host_name, db_name, user_name, user_password):
    """Creates the users table."""
    connection = None
    try:
        connection = mysql.connector.connect(host=host_name, database=db_name, user=user_name, password=user_password)
        cursor = connection.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        print("Users table created successfully")
    except Error as e:
        print(f"Error creating users table: '{e}'")
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()
            # print("MySQL connection for users is closed")

def create_user_tracked_games_table(host_name, db_name, user_name, user_password):
    """Creates the user_tracked_games table with foreign keys."""
    connection = None
    try:
        connection = mysql.connector.connect(host=host_name, database=db_name, user=user_name, password=user_password)
        cursor = connection.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS user_tracked_games (
            user_id INT NOT NULL,
            game_igdb_id INT NOT NULL,
            status VARCHAR(20) DEFAULT 'Planned',
            personal_rating INT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            PRIMARY KEY (user_id, game_igdb_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (game_igdb_id) REFERENCES local_games(igdb_id) ON DELETE CASCADE
        );
        """
        cursor.execute(create_table_query)
        print("User_tracked_games table created successfully")
    except Error as e:
        print(f"Error creating user_tracked_games table: '{e}'")
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()
            # print("MySQL connection for user_tracked_games is closed")


if __name__ == "__main__":
    host_name = 'localhost'
    db_name = 'gametrackerV2'
    user_name = 'root'
    user_password = 'password'

    # Create all tables if the script is run directly
    # Note: Order matters due to foreign key constraints
    create_games_table(host_name, db_name, user_name, user_password) # If games table is needed independently
    create_local_games_table(host_name, db_name, user_name, user_password) # Must exist before user_tracked_games FK
    create_users_table(host_name, db_name, user_name, user_password) # Must exist before user_tracked_games FK
    create_user_tracked_games_table(host_name, db_name, user_name, user_password) # Depends on users and local_games
    print("All table creation attempts finished.")