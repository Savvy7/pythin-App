from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models.game import search_local_games, get_all_games, get_game_details
from app.models.game import get_user_game_data, update_game_status, get_user_library_game_ids
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
        return render_template('search_results.html', games=[], logged_in=('user_id' in session))
    
    # First, search in the local database
    local_results = search_local_games(query)
    if local_results:
        print(f"Found {len(local_results)} games in local database for query: '{query}'")
        return render_template('search_results.html', games=local_results, logged_in=('user_id' in session))
        
    # If no local results, then query the IGDB API
    print(f"No local results found. Searching IGDB API for games with query: '{query}'")
    game_data = search_games(query)
    
    if not game_data:
        flash(f"No games found for '{query}'", "info")
        return render_template('search_results.html', games=[], logged_in=('user_id' in session))
        
    return render_template('search_results.html', games=game_data, logged_in=('user_id' in session))

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
        formatted_game = {
            'id': None,  # We don't use this, it's the internal DB ID
            'igdb_id': game['id'],
            'title': game['name'],
            'cover': game['cover']['url'] if game['cover'] and game['cover']['url'] else None,
            'release_date': game['release_dates']['human'] if 'release_dates' in game and game['release_dates'] else None,
            'summary': game['summary'],
            'genres': [genre['name'] for genre in game['genres']] if game['genres'] else [],
            'platforms': [],  # Not included in basic search results
            'rating': None,
            'weighted_rating': None
        }
        games.append(formatted_game)
    
    # Get unique list of genres and platforms for filters
    all_genres = set()
    all_platforms = set()
    for game in games:
        for genre in game['genres']:
            all_genres.add(genre)
    
    # Get user's library game IDs if user is logged in
    user_library_ids = []
    if 'user_id' in session:
        user_library_ids = get_user_library_game_ids(session['user_id'])
    
    return render_template('all_games.html',
                          games=games,
                          genres=sorted(all_genres),
                          platforms=sorted(all_platforms),
                          user_library_ids=user_library_ids,
                          search_query=query,
                          logged_in=('user_id' in session))

@games_bp.route('/<int:igdb_id>')
@login_required
def game_details(igdb_id):
    """Display detailed information about a specific game."""
    game_data = get_game_details(igdb_id)
    
    if not game_data:
        flash("Game not found in database", "warning")
        return redirect(url_for('games.all_games'))
    
    # Get user-specific data for this game
    user_id = session['user_id']
    user_data = get_user_game_data(user_id, igdb_id)
    
    # Pass game data and user data to the template
    return render_template('game_details.html', 
                          game=game_data, 
                          user_data=user_data,
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
    
    return redirect(url_for('games.game_details', igdb_id=igdb_id))
