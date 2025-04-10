import mysql.connector
from mysql.connector import Error
import json
import requests
import time

# Database credentials
DB_HOST = 'localhost'
DB_NAME = 'gametrackerV2'
DB_USER = 'root'
DB_PASSWORD = 'password'

# Bayesian parameters for weighted rating
MIN_VOTES = 1000  # m
C = 70  # Estimated average rating

def weighted_rating(R, v, m=MIN_VOTES, C=C):
    """Calculate weighted rating using Bayesian average"""
    return (v / (v + m)) * R + (m / (v + m)) * C

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
    query = f'''
    fields id, name, total_rating, total_rating_count, cover.url, release_dates.human,
        platforms.name, genres.name, summary, rating,
        involved_companies.developer, involved_companies.publisher, involved_companies.company.name,
        game_modes.name, collections.name, franchises.name, themes.name, game_engines.name;
    where id = {igdb_id};
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
        connection = mysql.connector.connect(
            host=host_name,
            database=db_name,
            user=user_name,
            password=user_password
        )
        cursor = connection.cursor()
        
        # Insert or update the game
        insert_query = """
        INSERT INTO local_games (
            igdb_id, title, cover, release_date, platforms, genres, rating, summary, metadata,
            developer, publisher, tags
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            publisher = VALUES(publisher)
        """
        
        cursor.execute(insert_query, (
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
            json.dumps([])  # Placeholder for tags
        ))
        
        connection.commit()
        print(f"Successfully added/updated game '{game['name']}' (ID: {game['id']}) to local_games table.")
        return game
        
    except Error as e:
        print(f"Error adding game to database: {e}")
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
        connection = mysql.connector.connect(
            host=host_name,
            database=db_name,
            user=user_name,
            password=user_password
        )
        cursor = connection.cursor()

        for game in game_data:
            # Use the new function for each game
            client_id = "5z3ofm5nmm44s4y4fwtidim7pp9vig"
            client_secret = "efuidgsvskkdqj0rk57s7nyodtgo72"
            
            # Import here to avoid circular imports
            import igdb_api
            access_token = igdb_api.get_igdb_access_token(client_id, client_secret)
            
            # Add each game
            add_game_to_db(game['id'], client_id, access_token, host_name, db_name, user_name, user_password)

        print("Game data loaded into the database successfully")
    except Error as e:
        print(f"Error: '{e}'")
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

if __name__ == "__main__":
    host_name = 'localhost'
    db_name = 'gametrackerV2'
    user_name = 'root'
    user_password = 'password'

    # Load game data from IGDB API
    import igdb_api
    client_id = "5z3ofm5nmm44s4y4fwtidim7pp9vig"
    client_secret = "efuidgsvskkdqj0rk57s7nyodtgo72"
    access_token = igdb_api.get_igdb_access_token(client_id, client_secret)
    query = "Cyberpunk"
    game_data = igdb_api.get_igdb_games(query, client_id, access_token)

    if game_data:
        load_game_data_to_db(host_name, db_name, user_name, user_password, game_data)