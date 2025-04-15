from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models.game import search_local_games, get_all_games, get_game_details, get_user_game_data, update_game_status, get_user_library_game_ids
from app.services.igdb_service import search_games, add_game_to_database
from app.utils.decorators import login_required

games_bp = Blueprint('games', __name__, url_prefix='/games')

@games_bp.route('/')
def all_games():
    """Display all games in the database."""
    games = get_all_games()
    
    # Get unique list of genres and platforms for filters
    all_genres = set()
    all_platforms = set()
    for game in games:
        for genre in game['genres']:
            all_genres.add(genre)
        for platform in game['platforms']:
            all_platforms.add(platform)
    
    # Get user's library game IDs for "Add to Library" button logic
    user_library_ids = []
    if 'user_id' in session:
        user_library_ids = get_user_library_game_ids(session['user_id'])
            
    return render_template('all_games.html', 
                          games=games, 
                          genres=sorted(all_genres),
                          platforms=sorted(all_platforms),
                          user_library_ids=user_library_ids,
                          logged_in=('user_id' in session))

@games_bp.route('/search')
def search():
    """Search for games in both local DB and IGDB."""
    query = request.args.get('query')
    if not query:
        return render_template('search_results.html', 
                               games=[], 
                               genres=[], 
                               platforms=[], 
                               user_library_ids=[],
                               search_query=query,
                               logged_in=('user_id' in session))
    
    # Search local database first
    game_results = search_local_games(query) # Returns IGDB-like format
    
    # If no local results, query IGDB API
    if not game_results:
        print(f"No local results found. Searching IGDB API for games with query: '{query}'")
        game_results = search_games(query) # Returns IGDB-like format
    
    # Handle no results found
    if not game_results:
        flash(f"No games found for '{query}'", "info")
        return render_template('search_results.html', 
                               games=[], 
                               genres=[], 
                               platforms=[], 
                               user_library_ids=[],
                               search_query=query,
                               logged_in=('user_id' in session))

    # Prepare data for the template (similar to all_games)
    games_for_template = []
    all_genres = set()
    all_platforms = set()
    
    for game in game_results:
        # Extract data needed for the template (including filter data)
        genres = [genre.get('name') for genre in game.get('genres', []) if genre.get('name')]
        
        # Get platforms from either the platform_names field or by extracting from platforms
        if hasattr(game, 'platform_names') and game.platform_names:
            platforms = game.platform_names
        else:
            platforms = [platform.get('name') for platform in game.get('platforms', []) if platform.get('name')]
        
        # Handle release dates which could be a list or a dict
        release_date = None
        if hasattr(game, 'release_date') and game.release_date:
            release_date = game.release_date
        else:
            release_dates = game.get('release_dates')
            if release_dates:
                if isinstance(release_dates, dict) and 'human' in release_dates:
                    release_date = release_dates['human']
                elif isinstance(release_dates, list) and len(release_dates) > 0:
                    # Get the first release date that has a 'human' field
                    for date_entry in release_dates:
                        if isinstance(date_entry, dict) and 'human' in date_entry:
                            release_date = date_entry['human']
                            break
        
        formatted_game = {
            'id': game.get('id'), # Used for add_game link
            'igdb_id': game.get('id'), # Consistency, might be useful
            'title': game.get('name'),
            'cover': game.get('cover', {}).get('url') if game.get('cover') else None,
            'release_date': release_date,
            'summary': game.get('summary'),
            'genres': genres,
            'platforms': platforms,
            'rating': game.get('rating'), # Assuming search_games returns these
            'weighted_rating': game.get('total_rating'), # Assuming search_games returns these
             # Fields needed for all_games style rendering
            'cover_url': game.get('cover', {}).get('url') if game.get('cover') else None, 
            'genre_names': genres,
            'name': game.get('name'), # Needed for backward compatibility with search_results.html
        }
        games_for_template.append(formatted_game)
        
        for genre in genres:
            all_genres.add(genre)
        for platform in platforms:
            all_platforms.add(platform)

    # Get user's library game IDs
    user_library_ids = []
    if 'user_id' in session:
        user_library_ids = get_user_library_game_ids(session['user_id'])

    return render_template('search_results.html', 
                          games=games_for_template, 
                          genres=sorted(all_genres),
                          platforms=sorted(all_platforms), # Pass platforms
                          user_library_ids=user_library_ids,
                          search_query=query,
                          logged_in=('user_id' in session))

@games_bp.route('/search_local')
def search_local():
    """Search for games in the local database only."""
    query = request.args.get('query', '')
    
    if not query:
        return redirect(url_for('games.all_games'))
    
    # Get formatted results from local database
    games_igdb_format = search_local_games(query)
    
    # Convert back to the format expected by all_games.html
    games = []
    
    for game in games_igdb_format:
        # Convert from IGDB API format to the format expected by all_games.html
        genres = [genre.get('name') for genre in game.get('genres', []) if genre.get('name')]
        # Assuming platforms are not reliably in local search results formatted this way
        platforms = [] 
        
        # Handle release dates which could be a list or a dict
        release_date = None
        release_dates = game.get('release_dates')
        if release_dates:
            if isinstance(release_dates, dict) and 'human' in release_dates:
                release_date = release_dates['human']
            elif isinstance(release_dates, list) and len(release_dates) > 0:
                # Get the first release date that has a 'human' field
                for date_entry in release_dates:
                    if isinstance(date_entry, dict) and 'human' in date_entry:
                        release_date = date_entry['human']
                        break
        
        formatted_game = {
            'id': None,  # We don't use this, it's the internal DB ID
            'igdb_id': game.get('id'),
            'title': game.get('name'),
            'cover': game.get('cover', {}).get('url') if game.get('cover') else None,
            'release_date': release_date,
            'summary': game.get('summary'),
            'genres': genres,
            'platforms': platforms, # Keep platforms empty for local search?
            'rating': None, # Local search might not have rating
            'weighted_rating': None # Local search might not have weighted_rating
        }
        games.append(formatted_game)
    
    # Get unique list of genres and platforms for filters
    all_genres = set()
    all_platforms = set() # Keep platforms empty for local search?
    for game in games:
        for genre in game['genres']:
            all_genres.add(genre)
    
    # Get user's library game IDs if user is logged in
    user_library_ids = []
    if 'user_id' in session:
        user_library_ids = get_user_library_game_ids(session['user_id'])
    
    # Renders all_games.html, which expects this data
    return render_template('all_games.html',
                          games=games,
                          genres=sorted(all_genres),
                          platforms=sorted(all_platforms), # Pass empty platforms
                          user_library_ids=user_library_ids,
                          search_query=query,
                          logged_in=('user_id' in session))

@games_bp.route('/<int:igdb_id>')
@login_required
def game_details(igdb_id):
    """Display detailed information about a specific game."""
    game_data = get_game_details(igdb_id)
    
    if not game_data:
        # Game not found in local database, fetch from IGDB and add to local database
        game_data = add_game_to_database(igdb_id)
        
        if not game_data:
            flash("Game not found or could not be retrieved from IGDB", "warning")
            return redirect(url_for('games.all_games'))
        
        # The game was added to database - now retrieve it in the expected format
        game_data = get_game_details(igdb_id)
        
        if not game_data:
            flash("Game was added but could not be retrieved from local database", "warning")
            return redirect(url_for('games.all_games'))
    
    # Get user-specific data for this game
    user_id = session['user_id']
    user_data = get_user_game_data(user_id, igdb_id)
    
    # Set default values for template variables
    in_library = False
    library_status = 'Planning'
    personal_rating = 0
    review = ''
    
    # If user data exists, populate the variables
    if user_data:
        in_library = True
        library_status = user_data.get('status', 'Planning')
        personal_rating = user_data.get('personal_rating', 0)
        review = user_data.get('review', '')
    
    # Pass game data and user data to the template
    return render_template('game_details.html', 
                          game=game_data, 
                          user_data=user_data,
                          in_library=in_library,
                          library_status=library_status,
                          personal_rating=personal_rating,
                          review=review,
                          logged_in=True)

@games_bp.route('/update_status/<int:igdb_id>', methods=['POST'])
@login_required
def update_game_status_route(igdb_id):
    """Updates the status, rating, and review of a tracked game."""
    user_id = session['user_id']
    status = request.form.get('status')
    rating = request.form.get('rating')
    review = request.form.get('review')
    
    success = update_game_status(user_id, igdb_id, status, rating, review)
    
    if success:
        flash("Game status updated successfully!", "success")
    else:
        flash("No changes were made or game not found.", "warning")
    
    # Check if a return_to parameter is provided or if referrer indicates the library page
    return_to = request.form.get('return_to')
    referrer = request.referrer
    
    if return_to == 'library':
        return redirect(url_for('library.my_library'))
    elif referrer and 'library' in referrer:
        return redirect(url_for('library.my_library'))
    else:
        return redirect(url_for('games.game_details', igdb_id=igdb_id))
