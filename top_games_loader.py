import requests
import mysql.connector
from mysql.connector import Error
import json
import time
import igdb_api # Import our existing module

# IGDB API credentials (Can be removed if fetched from igdb_api module context, but keep for now)
CLIENT_ID = "5z3ofm5nmm44s4y4fwtidim7pp9vig"
CLIENT_SECRET = "xvlwctmsktbu6vz6gwwd2n6w0um4ow" # Ensure this is the correct active secret

# Database credentials
DB_HOST = 'localhost'
DB_NAME = 'gametrackerV2'
DB_USER = 'root'
DB_PASSWORD = 'password'

# Bayesian parameters for weighted rating
MIN_VOTES = 1000  # m
C = 70            # Estimated average rating across all games

# Remove local get_igdb_access_token function, use the one from igdb_api.py

def weighted_rating(R, v, m=MIN_VOTES, C=C):
    """Calculate weighted rating using Bayesian average"""
    return (v / (v + m)) * R + (m / (v + m)) * C

def fetch_top_games(access_token):
    """Fetch top games from IGDB"""
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }

    # Query to get games with ratings and additional details, excluding versions/DLCs
 # Query to get games with ratings and additional details, excluding versions/DLCs
    query = '''
       fields id, name, total_rating, total_rating_count, cover.url, release_dates.human,
           platforms.name, genres.name, summary, rating,
           involved_companies.developer, involved_companies.publisher, involved_companies.company.name, 
           game_modes.name, collections.name, franchises.name, themes.name, game_engines.name;
    where total_rating != null & total_rating_count >= 50 & version_parent = null;
    sort total_rating desc;
    limit 500; 
    '''

    url = 'https://api.igdb.com/v4/games'
    response = requests.post(url, headers=headers, data=query)

    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return []

    games = response.json()
    
    # Add weighted score and process data
    for game in games:
        R = game['total_rating']
        v = game['total_rating_count']
        game['weighted_rating'] = weighted_rating(R, v)
        
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
        game['developer'] = developer_names[0] if developer_names else None # Store first developer
        game['publisher'] = publisher_names[0] if publisher_names else None # Store first publisher

        # Extract names for other fields
        game['game_modes'] = [mode['name'] for mode in game.get('game_modes', [])]
        game['series'] = [coll['name'] for coll in game.get('collections', [])] # Using collections as series
        game['franchises'] = [fran['name'] for fran in game.get('franchises', [])]
        game['themes'] = [theme['name'] for theme in game.get('themes', [])]
        game['game_engines'] = [eng['name'] for eng in game.get('game_engines', [])]


    # Sort by weighted rating and get top 100
    return sorted(games, key=lambda x: x['weighted_rating'], reverse=True)[:500]

def add_game_to_db(igdb_id, access_token):
    """Fetches a game by ID from IGDB and adds it to the local_games table"""
    # Fetch the game details from IGDB
    headers = {
        'Client-ID': CLIENT_ID,
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
        return False
    
    games = response.json()
    if not games:
        print(f"Game with ID {igdb_id} not found")
        return False
    
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
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor()
        
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
            json.dumps(game.get('game_modes', [])),
            json.dumps(game.get('series', [])),
            json.dumps(game.get('franchises', [])),
            json.dumps(game.get('themes', [])),
            json.dumps(game.get('game_engines', [])),
            # json.dumps([]),  # Placeholder for tags
            game.get('weighted_rating')
        ))
        
        connection.commit()
        print(f"Successfully added/updated game '{game['name']}' (ID: {game['id']}) to local_games table.")
        return True
        
    except Error as e:
        print(f"Error adding game to database: {e}")
        return False
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()

def store_games_in_db(games):
    """Drops, Creates, and Stores games in the local_games table"""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor()

        # # Drop existing table
        # print("Dropping existing local_games table (if exists)...")
        # cursor.execute("DROP TABLE IF EXISTS local_games")

        # # Create new table with updated schema
        # print("Creating new local_games table...")
        # create_table_query = """
        # CREATE TABLE local_games (
        #     id INT AUTO_INCREMENT PRIMARY KEY,
        #     title TEXT NOT NULL,
        #     igdb_id INT UNIQUE,
        #     cover TEXT,
        #     release_date TEXT,
        #     platforms JSON,
        #     genres JSON,
        #     rating INT,
        #     summary TEXT,
        #     metadata JSON,
        #     developer TEXT,
        #     publisher TEXT,
        #     game_modes JSON,
        #     series JSON,
        #     franchises JSON,
        #     themes JSON,
        #     game_engines JSON,
        #     weighted_rating FLOAT
        # )
        # """
        # cursor.execute(create_table_query)
        # print("Local_games table created successfully.")

        # Insert new games
        print(f"Inserting {len(games)} games...")
        insert_query = """
        INSERT INTO local_games (
            igdb_id, title, cover, release_date, platforms, genres, rating, summary, metadata,
            developer, publisher, game_modes, series, franchises, themes, game_engines, weighted_rating
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values_list = []
        for game in games:
             values_list.append((
                game['id'],
                game['name'],
                game.get('cover'),
                game.get('release_date'),
                json.dumps(game.get('platforms', [])),
                json.dumps(game.get('genres', [])),
                game.get('rating'),
                game.get('summary'),
                json.dumps(game), # Store full fetched data as metadata
                game.get('developer'),
                game.get('publisher'),
                json.dumps(game.get('game_modes', [])),
                json.dumps(game.get('series', [])),
                json.dumps(game.get('franchises', [])),
                json.dumps(game.get('themes', [])),
                json.dumps(game.get('game_engines', [])),
                  # Placeholder for tags
                game['weighted_rating']
            ))

        cursor.executemany(insert_query, values_list)
        connection.commit()
        print(f"Successfully inserted {cursor.rowcount} games into local_games table.")

    except Error as e:
        print(f"Error during database operation: {e}")
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()

def main():
    print("Starting top games loader...")
    
    # Get IGDB access token using the imported function
    print("Getting IGDB access token...")
    # Make sure CLIENT_ID and CLIENT_SECRET are correct
    access_token = igdb_api.get_igdb_access_token(CLIENT_ID, CLIENT_SECRET)
    
    if not access_token:
        print("Failed to get access token. Exiting.")
        return

    # Fetch top games
    print("Fetching top games from IGDB...")
    top_games = fetch_top_games(access_token)
    
    # Store games in database
    print("Storing games in database...")
    store_games_in_db(top_games)
    
    print("Process completed successfully!")

if __name__ == "__main__":
    main() 