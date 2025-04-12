import json
from mysql.connector import Error
from app.models.db import get_db_connection
import os

# IGDB API credentials from environment variables
IGDB_CLIENT_ID = os.getenv('IGDB_CLIENT_ID')
IGDB_CLIENT_SECRET = os.getenv('IGDB_CLIENT_SECRET')

def search_local_games(query):
    """Search for games in the local database based on a query string."""
    conn = get_db_connection()
    if not conn:
        return []
        
    cursor = conn.cursor(dictionary=True)
    games = []
    
    try:
        # Search by title with LIKE for partial matching
        search_query = f"%{query}%"
        cursor.execute(
            "SELECT * FROM local_games WHERE title LIKE %s ORDER BY title ASC",
            (search_query,)
        )
        db_games = cursor.fetchall()
        
        # Format results to match IGDB API format
        for game in db_games:
            # Parse genres from JSON
            genres = []
            if game['genres']:
                try:
                    if isinstance(game['genres'], str):
                        genres_data = json.loads(game['genres'])
                    else:
                        genres_data = game['genres']
                    genres = genres_data
                except (json.JSONDecodeError, TypeError):
                    genres = []
            
            # Create a new object with IGDB-like structure
            formatted_game = {
                'id': game['igdb_id'],         # Use IGDB ID as the ID
                'name': game['title'],         # Map title to name
                'cover': {
                    'url': game['cover'] if game['cover'] else None
                },
                'release_dates': {
                    'human': game['release_date']
                },
                'summary': game['summary'],
                'genres': [{'name': genre} for genre in genres]
            }
            
            games.append(formatted_game)
    
    except Error as e:
        print(f"Error searching local games: {e}")
    finally:
        cursor.close()
        conn.close()
        
    return games

def get_all_games():
    """Get all games from the database."""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    games = []
    
    try:
        # Get all games from the database
        cursor.execute("SELECT * FROM local_games ORDER BY title ASC")
        db_games = cursor.fetchall()
        
        # Parse and format all games consistently
        for game in db_games:
            # Parse JSON fields
            parsed_genres = []
            parsed_platforms = []
            
            if game['genres']:
                try:
                    if isinstance(game['genres'], str):
                        parsed_genres = json.loads(game['genres'])
                    else:
                        parsed_genres = game['genres']
                except (json.JSONDecodeError, TypeError):
                    parsed_genres = []
                    
            if game['platforms']:
                try:
                    if isinstance(game['platforms'], str):
                        parsed_platforms = json.loads(game['platforms'])
                    else:
                        parsed_platforms = game['platforms']
                except (json.JSONDecodeError, TypeError):
                    parsed_platforms = []
            
            # Format game consistently with search results
            formatted_game = {
                'id': game['id'],
                'igdb_id': game['igdb_id'],
                'title': game['title'],
                'cover': game['cover'],
                'release_date': game['release_date'],
                'summary': game['summary'],
                'genres': parsed_genres,
                'platforms': parsed_platforms,
                'rating': game['rating'],
                'weighted_rating': game['weighted_rating']
            }
            
            games.append(formatted_game)
    except Error as e:
        print(f"Error retrieving games: {e}")
    finally:
        cursor.close()
        conn.close()
        
    return games

def get_game_details(igdb_id):
    """Get detailed information about a specific game."""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    game_data = None
    
    try:
        # Get game data from local_games table
        game_query = """
        SELECT * FROM local_games
        WHERE igdb_id = %s
        """
        cursor.execute(game_query, (igdb_id,))
        game_data = cursor.fetchone()
        
        if not game_data:
            return None
            
        # Parse JSON fields
        json_fields = ['platforms', 'genres', 'game_modes', 'series', 'franchises', 'themes', 'game_engines', 'tags']
        for field in json_fields:
            if field in game_data and game_data[field]:
                try:
                    # If it's already a string, try to parse it to JSON
                    if isinstance(game_data[field], str):
                        game_data[field] = json.loads(game_data[field])
                    # If parsing fails or it's None, ensure it's an empty list
                except (json.JSONDecodeError, TypeError):
                    game_data[field] = []
            else:
                game_data[field] = []
                
    except Error as e:
        print(f"Error retrieving game details for game {igdb_id}: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return game_data

def get_user_game_data(user_id, igdb_id):
    """Get user-specific data for a game."""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    user_data = None
    
    try:
        # Get user-specific data for this game
        user_query = """
        SELECT status, personal_rating, review, date_added 
        FROM user_tracked_games
        WHERE user_id = %s AND game_igdb_id = %s
        """
        cursor.execute(user_query, (user_id, igdb_id))
        user_data = cursor.fetchone()
    except Error as e:
        print(f"Error retrieving user game data for user {user_id}, game {igdb_id}: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return user_data

def add_game_to_user_library(user_id, igdb_id):
    """Add a game to the user's tracked games."""
    connection = get_db_connection()
    if not connection:
        return False
        
    success = False
    try:
        cursor = connection.cursor()
        
        # Insert with default status ('Wishlist')
        cursor.execute(
            "INSERT INTO user_tracked_games (user_id, game_igdb_id) VALUES (%s, %s)",
            (user_id, igdb_id)
        )
        connection.commit()
        success = True
    except Error as e:
        print(f"Database error adding game to library: {e}")
        connection.rollback()
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()
    
    return success

def update_game_status(user_id, igdb_id, status, rating, review):
    """Updates the status, rating, and review of a tracked game."""
    conn = get_db_connection()
    if not conn:
        return False
    
    success = False
    try:
        cursor = conn.cursor()
        # Update the user's tracked game entry
        query = """
        UPDATE user_tracked_games 
        SET status = %s, personal_rating = %s, review = %s
        WHERE user_id = %s AND game_igdb_id = %s
        """
        cursor.execute(query, (status, rating, review, user_id, igdb_id))
        conn.commit()
        
        success = cursor.rowcount > 0
    except Error as e:
        conn.rollback()
        print(f"Error updating game status for user {user_id}, game {igdb_id}: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return success

def remove_game_from_library(user_id, igdb_id):
    """Removes a game from the user's tracked games."""
    conn = get_db_connection()
    if not conn:
        return False
    
    success = False
    try:
        cursor = conn.cursor()
        # Delete the user's tracked game entry
        query = """
        DELETE FROM user_tracked_games
        WHERE user_id = %s AND game_igdb_id = %s
        """
        cursor.execute(query, (user_id, igdb_id))
        conn.commit()
        
        success = cursor.rowcount > 0
    except Error as e:
        conn.rollback()
        print(f"Error removing game for user {user_id}, game {igdb_id}: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return success

def get_user_library(user_id):
    """Gets all games tracked by a user."""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    tracked_games = []
    
    try:
        # Query joining user_tracked_games with local_games
        query = """
        SELECT
            lg.*,  -- Select all columns from local_games
            utg.status,
            utg.personal_rating,
            utg.date_added,
            utg.review
        FROM user_tracked_games utg
        JOIN local_games lg ON utg.game_igdb_id = lg.igdb_id
        WHERE utg.user_id = %s
        ORDER BY utg.date_added DESC;
        """
        cursor.execute(query, (user_id,))
        tracked_games = cursor.fetchall()
        
        # Parse JSON fields
        for game in tracked_games:
            json_fields = ['platforms', 'genres', 'game_modes', 'series', 'franchises', 'themes', 'game_engines', 'tags']
            for field in json_fields:
                if field in game and game[field]:
                    try:
                        if isinstance(game[field], str):
                            game[field] = json.loads(game[field])
                    except (json.JSONDecodeError, TypeError):
                        game[field] = []
                else:
                    game[field] = []
    except Error as e:
        print(f"Error fetching library for user {user_id}: {e}")
    finally:
        cursor.close()
        conn.close()
        
    return tracked_games

def get_user_library_game_ids(user_id):
    """Get list of game IDs in user's library."""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    user_library_ids = []
    
    try:
        cursor.execute(
            "SELECT game_igdb_id FROM user_tracked_games WHERE user_id = %s",
            (user_id,)
        )
        user_library = cursor.fetchall()
        user_library_ids = [game['game_igdb_id'] for game in user_library]
    except Error as e:
        print(f"Error fetching library game IDs for user {user_id}: {e}")
    finally:
        cursor.close()
        conn.close()
        
    return user_library_ids
