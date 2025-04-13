import mysql.connector
from mysql.connector import Error
import json
import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database credentials from environment variables
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'gametrackerV2')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

# IGDB API credentials from environment variables
IGDB_CLIENT_ID = os.getenv('IGDB_CLIENT_ID')
IGDB_CLIENT_SECRET = os.getenv('IGDB_CLIENT_SECRET')

# Bayesian parameters for weighted rating
MIN_VOTES = 1000  # m
C = 70  # Estimated average rating

def weighted_rating(R, v, m=MIN_VOTES, C=C):
    """Calculate weighted rating using Bayesian average"""
    return (v / (v + m)) * R + (m / (v + m)) * C

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

def add_game_to_db(igdb_id, client_id, access_token, host_name=DB_HOST, db_name=DB_NAME, user_name=DB_USER, user_password=DB_PASSWORD):
    """Fetches a game by ID from IGDB and adds it to the local_games table.
    
    Args:
        igdb_id: The IGDB ID of the game to fetch
        client_id: The IGDB API client ID
        access_token: The IGDB API access token
        host_name: MySQL host (default: DB_HOST)
        db_name: MySQL database name (default: DB_NAME)
        user_name: MySQL username (default: DB_USER)
        user_password: MySQL password (default: DB_PASSWORD)
        
    Returns:
        dict: The game data that was added to the database, or None if failed
    """
    # Fetch the game details from IGDB
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    
    # Query to get detailed game data based on ID
    # Only fetch main games (category=0), not DLCs or expansions
    query = f'''
    fields id, name, total_rating, total_rating_count, cover.url, release_dates.human,
        platforms.name, genres.name, summary, rating, category,
        involved_companies.developer, involved_companies.publisher, involved_companies.company.name,
        game_modes.name, collections.name, franchises.name, themes.name, game_engines.name;
    where id = {igdb_id} & (category = 0 | category = null);
    '''
    
    url = 'https://api.igdb.com/v4/games'
    response = requests.post(url, headers=headers, data=query)
    
    if response.status_code != 200:
        print(f"Error fetching game {igdb_id}:", response.status_code, response.text)
        return None
    
    games = response.json()
    if not games:
        print(f"Game with ID {igdb_id} not found")
        return None
    
    # Process the game data
    game = games[0]
    print(f"Processing game: {game.get('name')} (ID: {game.get('id')})")
    
    # Process platforms and genres into lists
    game['platforms'] = [p['name'] for p in game.get('platforms', [])]
    game['genres'] = [g['name'] for g in game.get('genres', [])]
    
    # Get release date
    game['release_date'] = game.get('release_dates', [{}])[0].get('human')
    
    # Get cover URL
    game['cover'] = game.get('cover', {}).get('url')
    
    # Extract developer and publisher names
    developer_names = [comp['company']['name'] for comp in game.get('involved_companies', []) if comp.get('developer')]
    publisher_names = [comp['company']['name'] for comp in game.get('involved_companies', []) if comp.get('publisher')]
    game['developer'] = developer_names[0] if developer_names else None  # Store first developer
    game['publisher'] = publisher_names[0] if publisher_names else None  # Store first publisher
    
    # Extract names for other fields
    game['game_modes'] = [mode['name'] for mode in game.get('game_modes', [])]
    game['series'] = [coll['name'] for coll in game.get('collections', [])]  # Using collections as series
    game['franchises'] = [fran['name'] for fran in game.get('franchises', [])]
    game['themes'] = [theme['name'] for theme in game.get('themes', [])]
    game['game_engines'] = [eng['name'] for eng in game.get('game_engines', [])]
    
    # Calculate weighted rating if ratings exist
    if 'total_rating' in game and 'total_rating_count' in game:
        R = game['total_rating']
        v = game['total_rating_count']
        game['weighted_rating'] = weighted_rating(R, v)
    else:
        game['weighted_rating'] = None
    
    # Now store the game in the database
    connection = None
    try:
        connection = get_db_connection()
        if not connection:
            print("Failed to connect to database")
            return None
            
        cursor = connection.cursor()
        
        # Check if the table exists and has the correct structure
        cursor.execute("SHOW TABLES LIKE 'local_games'")
        if not cursor.fetchone():
            # Create the table if it doesn't exist
            create_table_query = """
            CREATE TABLE local_games (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title TEXT NOT NULL,
                igdb_id INT UNIQUE,
                cover TEXT,
                release_date TEXT,
                platforms JSON,
                genres JSON,
                rating INT,
                summary TEXT,
                metadata JSON,
                developer TEXT,
                publisher TEXT,
                game_modes JSON,
                series JSON,
                franchises JSON,
                themes JSON,
                game_engines JSON,
                tags JSON,
                weighted_rating FLOAT
            )
            """
            cursor.execute(create_table_query)
            print("Created local_games table")
        
        # Insert or update the game
        insert_query = """
        INSERT INTO local_games (
            igdb_id, title, cover, release_date, platforms, genres, rating, summary, metadata,
            developer, publisher, game_modes, series, franchises, themes, game_engines, tags, weighted_rating
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            cover = VALUES(cover),
            release_date = VALUES(release_date),
            platforms = VALUES(platforms),
            genres = VALUES(genres),
            rating = VALUES(rating),
            summary = VALUES(summary),
            metadata = VALUES(metadata),
            developer = VALUES(developer),
            publisher = VALUES(publisher),
            game_modes = VALUES(game_modes),
            series = VALUES(series),
            franchises = VALUES(franchises),
            themes = VALUES(themes),
            game_engines = VALUES(game_engines),
            weighted_rating = VALUES(weighted_rating)
        """
        
        # Prepare the values
        values = (
            game['id'],
            game['name'],
            game.get('cover'),
            game.get('release_date'),
            json.dumps(game.get('platforms', [])),
            json.dumps(game.get('genres', [])),
            game.get('rating'),
            game.get('summary'),
            json.dumps(game),  # Store full fetched data as metadata
            game.get('developer'),
            game.get('publisher'),
            json.dumps(game.get('game_modes', [])),
            json.dumps(game.get('series', [])),
            json.dumps(game.get('franchises', [])),
            json.dumps(game.get('themes', [])),
            json.dumps(game.get('game_engines', [])),
            json.dumps([]),  # Placeholder for tags
            game.get('weighted_rating')
        )
        
        print(f"Attempting to insert game with values: {values}")
        cursor.execute(insert_query, values)
        connection.commit()
        print(f"Successfully added/updated game '{game['name']}' (ID: {game['id']}) to local_games table.")
        return game
        
    except Error as e:
        print(f"Error adding game to database: {e}")
        print(f"Error details: {str(e)}")
        if connection:
            connection.rollback()
        return None
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()

# Keep this function to maintain backwards compatibility if needed
def load_game_data_to_db(host_name, db_name, user_name, user_password, game_data):
    """Legacy function to load multiple games to database"""
    print("Warning: Using deprecated function. Consider using add_game_to_db instead.")
    connection = None
    try:
        connection = get_db_connection()
        if not connection:
            return

        for game in game_data:
            # Use the new function for each game
            add_game_to_db(
                game['id'], 
                IGDB_CLIENT_ID, 
                igdb_api.get_igdb_access_token(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET),
                host_name, 
                db_name, 
                user_name, 
                user_password
            )

        print("Game data loaded into the database successfully")
    except Error as e:
        print(f"Error: '{e}'")
    finally:
        if connection is not None and connection.is_connected():
            cursor = connection.cursor()
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

if __name__ == "__main__":
    # Load game data from IGDB API
    import igdb_api
    access_token = igdb_api.get_igdb_access_token(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)
    query = "Cyberpunk"
    game_data = igdb_api.get_igdb_games(query, IGDB_CLIENT_ID, access_token)

    if game_data:
        load_game_data_to_db(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, game_data)