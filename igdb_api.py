import requests

def get_igdb_access_token(client_id, client_secret):
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Failed to obtain access token: {response.status_code}")
        return None

def get_igdb_games(query, client_id, access_token):
    url = "https://api.igdb.com/v4/games"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    data = f"search \"{query}\"; fields id, name, cover.url, release_dates.human, platforms.name, genres.name, rating, summary;"

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve games using search: {response.status_code}, {response.text}") # Added more detail
        return None

def get_igdb_games_by_id(igdb_id, client_id, access_token):
    """Fetches a single game from IGDB by its ID."""
    url = "https://api.igdb.com/v4/games"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    # Query to fetch specific fields for a single game ID
    data = f"fields id, name, cover.url, release_dates.human, platforms.name, genres.name, rating, summary; where id = {igdb_id};"

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        result = response.json()
        # The API returns a list, even for a single ID match
        if result:
            return result[0] # Return the single game object
        else:
            print(f"No game found with IGDB ID: {igdb_id}")
            return None
    else:
        print(f"Failed to retrieve game by ID {igdb_id}: {response.status_code}, {response.text}") # Added more detail
        return None

if __name__ == "__main__":
    # Use the correct client_secret provided in the user message for app.py
    client_id = "5z3ofm5nmm44s4y4fwtidim7pp9vig"
    client_secret = "efuidgsvskkdqj0rk57s7nyodtgo72" # Make sure this is the active one
    access_token = get_igdb_access_token(client_id, client_secret)
    if access_token:
        query = "Cyberpunk"
        games = get_igdb_games(query, client_id, access_token)
        print(games)