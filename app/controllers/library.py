from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from app.models.game import get_user_library, add_game_to_user_library, remove_game_from_library
from app.services.igdb_service import add_game_to_database
from app.utils.decorators import login_required

library_bp = Blueprint('library', __name__, url_prefix='/library')

@library_bp.route('/')
@login_required
def my_library():
    """Displays the games tracked by the current user."""
    user_id = session['user_id']
    tracked_games = get_user_library(user_id)
            
    return render_template('my_library.html', library=tracked_games, logged_in=True)

@library_bp.route('/add/<int:igdb_id>')
@login_required
def add_game(igdb_id):
    """Add a game to the user's library."""
    # First ensure game exists in local database
    game = add_game_to_database(igdb_id)
    
    if not game:
        flash("Failed to add game. Could not retrieve game data from IGDB.", "danger")
        return redirect(url_for('games.all_games'))
    
    # Now add to user's tracked list
    user_id = session['user_id']
    success = add_game_to_user_library(user_id, igdb_id)
    
    if success:
        flash(f"Game '{game['name']}' added to your library!", "success")
    else:
        flash(f"Game '{game['name']}' is already in your library or couldn't be added.", "info")

    # Redirect based on the referrer
    referrer = request.referrer
    if referrer and 'search' in referrer:
        return redirect(url_for('games.search'))
    else:
        return redirect(url_for('library.my_library'))

@library_bp.route('/remove/<int:igdb_id>', methods=['POST'])
@login_required
def remove_game(igdb_id):
    """Removes a game from the user's tracked games."""
    user_id = session['user_id']
    
    success = remove_game_from_library(user_id, igdb_id)
    
    if success:
        flash("Game removed from your library.", "success")
    else:
        flash("Game not found in your library.", "warning")
    
    return redirect(url_for('library.my_library'))
