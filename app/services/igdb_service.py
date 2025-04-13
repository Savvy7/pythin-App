import os
import igdb_api
from data_loader import add_game_to_db

# IGDB API credentials from environment variables
IGDB_CLIENT_ID = os.getenv('IGDB_CLIENT_ID')
IGDB_CLIENT_SECRET = os.getenv('IGDB_CLIENT_SECRET')

# Global access token
access_token = None

def get_access_token():
    """Get or refresh IGDB access token."""
    global access_token
    if not access_token:
        access_token = igdb_api.get_igdb_access_token(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)
    return access_token

def search_games(query):
    """Search for games using IGDB API."""
    token = get_access_token()
    if not token:
        return None
    
    # Get games from IGDB API
    game_data = igdb_api.get_igdb_games(query, IGDB_CLIENT_ID, token)
    
    # Format results for consistent template rendering
    if game_data:
        for game in game_data:
            # If cover is an object with url, get the url directly
            if isinstance(game.get('cover'), dict) and 'url' in game['cover']:
                game['cover_url'] = game['cover']['url']
            else:
                game['cover_url'] = None
                
            # Get release date from nested object
            if 'release_dates' in game and game['release_dates'] and isinstance(game['release_dates'], list):
                # Handle release_dates as list
                for date in game['release_dates']:
                    if isinstance(date, dict) and 'human' in date:
                        game['release_date'] = date['human']
                        break
                else:
                    game['release_date'] = None
            elif 'release_dates' in game and game['release_dates'] and isinstance(game['release_dates'], dict) and 'human' in game['release_dates']:
                # Handle release_dates as dict
                game['release_date'] = game['release_dates']['human']
            else:
                game['release_date'] = None
                
            # Extract genre names
            game['genre_names'] = [genre['name'] for genre in game.get('genres', [])]
            
            # Extract platform names (now included in the API response)
            game['platform_names'] = [platform['name'] for platform in game.get('platforms', [])]
    
    return game_data

def add_game_to_database(igdb_id):
    """Add a game to the local database from IGDB."""
    token = get_access_token()
    if not token:
        return None
    
    # Use the data_loader function to add the game
    game = add_game_to_db(
        igdb_id,
        IGDB_CLIENT_ID,
        token
    )
    
    return game
