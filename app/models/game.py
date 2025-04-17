import json
from mysql.connector import Error
from app.models.db import get_db_connection, execute_transaction
import os

# IGDB API credentials from environment variables
IGDB_CLIENT_ID = os.getenv('IGDB_CLIENT_ID')
IGDB_CLIENT_SECRET = os.getenv('IGDB_CLIENT_SECRET')

def search_local_games(query):
    """Search for games in the local database based on a query string."""
    def transaction(conn, query):
        cursor = conn.cursor(dictionary=True)
        games = []
        
        try:
            # Search by title with LIKE for partial matching
            search_query = f"%{query}%"
            
            # Use prepared statement for security
            sql_query = "SELECT * FROM local_games WHERE title LIKE %s ORDER BY title ASC"
            cursor.execute(sql_query, (search_query,))
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
        finally:
            cursor.close()
            
        return games
    
    return execute_transaction(transaction, query) or []

def get_all_games():
    """Get all games from the database."""
    def transaction(conn):
        cursor = conn.cursor(dictionary=True)
        games = []
        
        try:
            # Get all games from the database with prepared statement
            query = "SELECT * FROM local_games ORDER BY title ASC"
            cursor.execute(query)
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
        finally:
            cursor.close()
            
        return games
    
    return execute_transaction(transaction) or []

def get_game_details(igdb_id):
    """Get detailed information about a specific game."""
    def transaction(conn, igdb_id):
        cursor = conn.cursor(dictionary=True)
        game_data = None
        
        try:
            # Get game data from local_games table with prepared statement
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
        finally:
            cursor.close()
        
        return game_data
    
    return execute_transaction(transaction, igdb_id)

def get_user_game_data(user_id, igdb_id):
    """Get user-specific data for a game."""
    def transaction(conn, user_id, igdb_id):
        cursor = conn.cursor(dictionary=True)
        user_data = None
        
        try:
            # Get user-specific data for this game with prepared statement
            user_query = """
            SELECT status, personal_rating, review, date_added 
            FROM user_tracked_games
            WHERE user_id = %s AND game_igdb_id = %s
            """
            cursor.execute(user_query, (user_id, igdb_id))
            user_data = cursor.fetchone()
        finally:
            cursor.close()
        
        return user_data
    
    return execute_transaction(transaction, user_id, igdb_id)

def add_game_to_user_library(user_id, igdb_id):
    """Add a game to the user's tracked games."""
    def transaction(conn, user_id, igdb_id):
        cursor = conn.cursor()
        success = False
        
        try:
            # Insert with default status ('Planning') using prepared statement
            query = "INSERT INTO user_tracked_games (user_id, game_igdb_id) VALUES (%s, %s)"
            cursor.execute(query, (user_id, igdb_id))
            success = True
        finally:
            cursor.close()
        
        return success
    
    return execute_transaction(transaction, user_id, igdb_id)

def update_game_status(user_id, igdb_id, status, rating, review):
    """Updates the status, rating, and review of a tracked game."""
    def transaction(conn, user_id, igdb_id, status, rating, review):
        cursor = conn.cursor()
        success = False
        
        try:
            # Update the user's tracked game entry with prepared statement
            query = """
            UPDATE user_tracked_games 
            SET status = %s, personal_rating = %s, review = %s
            WHERE user_id = %s AND game_igdb_id = %s
            """
            cursor.execute(query, (status, rating, review, user_id, igdb_id))
            success = cursor.rowcount > 0
        finally:
            cursor.close()
        
        return success
    
    return execute_transaction(transaction, user_id, igdb_id, status, rating, review)

def remove_game_from_library(user_id, igdb_id):
    """Removes a game from the user's tracked games."""
    def transaction(conn, user_id, igdb_id):
        cursor = conn.cursor()
        success = False
        
        try:
            # Delete the user's tracked game entry with prepared statement
            query = """
            DELETE FROM user_tracked_games
            WHERE user_id = %s AND game_igdb_id = %s
            """
            cursor.execute(query, (user_id, igdb_id))
            success = cursor.rowcount > 0
        finally:
            cursor.close()
        
        return success
    
    return execute_transaction(transaction, user_id, igdb_id)

def get_user_library(user_id):
    """Gets all games tracked by a user."""
    def transaction(conn, user_id):
        cursor = conn.cursor(dictionary=True)
        tracked_games = []
        
        try:
            # Query joining user_tracked_games with local_games using prepared statement
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
        finally:
            cursor.close()
            
        return tracked_games
    
    return execute_transaction(transaction, user_id) or []

def get_user_library_game_ids(user_id):
    """Get list of game IDs in user's library."""
    def transaction(conn, user_id):
        cursor = conn.cursor(dictionary=True)
        user_library_ids = []
        
        try:
            # Get game IDs with prepared statement
            query = "SELECT game_igdb_id FROM user_tracked_games WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            user_library = cursor.fetchall()
            user_library_ids = [game['game_igdb_id'] for game in user_library]
        finally:
            cursor.close()
            
        return user_library_ids
    
    return execute_transaction(transaction, user_id) or []
