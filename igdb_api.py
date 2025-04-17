import requests
import time
import os
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

# IGDB API credentials from environment variables
IGDB_CLIENT_ID = os.getenv('IGDB_CLIENT_ID')
IGDB_CLIENT_SECRET = os.getenv('IGDB_CLIENT_SECRET')

# Token cache
_token_cache = {
    'token': None,
    'expires_at': 0
}

def get_igdb_access_token(client_id=IGDB_CLIENT_ID, client_secret=IGDB_CLIENT_SECRET):
    """Get IGDB access token, using cached token if available and not expired"""
    # Get cached token from .env
    cached_token = os.getenv('IGDB_ACCESS_TOKEN')
    expires_at = float(os.getenv('IGDB_TOKEN_EXPIRES_AT', '0'))
    
    # # Check if we have a valid cached token
    current_time = time.time()
    if cached_token and current_time < expires_at:
        return cached_token
    
    # Get new token if cache is empty or expired
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    
    try:
        response = requests.post(url, params=params, verify=False)
        response.raise_for_status()
        data = response.json()
        
        # Cache the token with expiration time (usually 60 days, but we'll refresh after 30 days to be safe)
        new_expires_at = current_time + (30 * 24 * 60 * 60)  # 30 days in seconds
        
        # Save to .env file
        set_key('.env', 'IGDB_ACCESS_TOKEN', data["access_token"])
        set_key('.env', 'IGDB_TOKEN_EXPIRES_AT', str(new_expires_at))
        
        return data["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {e}")
        return None

def get_igdb_games(query, client_id=IGDB_CLIENT_ID, access_token=None):
    """Search for games using IGDB API"""
    if not access_token:
        access_token = get_igdb_access_token(client_id)
        if not access_token:
            return None
            
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    
    # Query to get basic game info
    # Category values in IGDB: 
    # 0 = main game, 1 = DLC, 2 = expansion, 3 = bundle, 4 = standalone_expansion, 
    # 5 = mod, 6 = episode, 7 = season, 8 = remake, 9 = remaster, 10 = expanded_game, 
    # 11 = port, 12 = fork, 13 = pack, 14 = update
    query_str = f'''
    fields id, name, cover.url, release_dates.human, summary, genres.name, platforms.name, rating, total_rating, category;
    search "{query}";
    where category = 0 & parent_game = null & version_parent = null;
    limit 10;
    '''
    
    url = 'https://api.igdb.com/v4/games'
    response = requests.post(url, headers=headers, data=query_str)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error searching games: {response.status_code} - {response.text}")
        return None

def get_igdb_games_by_id(game_id, client_id=IGDB_CLIENT_ID, access_token=None):
    """Get detailed game info by ID using IGDB API"""
    if not access_token:
        access_token = get_igdb_access_token(client_id)
        if not access_token:
            return None
            
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    
    # Query to get detailed game info
    query_str = f'''
    fields id, name, total_rating, total_rating_count, cover.url, release_dates.human,
        platforms.name, genres.name, summary, rating,
        involved_companies.developer, involved_companies.publisher, involved_companies.company.name,
        game_modes.name, collections.name, franchises.name, themes.name, game_engines.name;
    where id = {game_id};
    '''
    
    url = 'https://api.igdb.com/v4/games'
    response = requests.post(url, headers=headers, data=query_str)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting game by ID: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    access_token = get_igdb_access_token()
    if access_token:
        query = "Cyberpunk"
        games = get_igdb_games(query)
        print(games)