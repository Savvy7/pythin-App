from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import json
import functools # For login_required decorator
import os # To generate secret key
import igdb_api
from data_loader import add_game_to_db, get_db_connection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Custom Jinja2 filters
@app.template_filter('fromjson')
def fromjson(value):
    """Parse a JSON string into Python objects for use in templates."""
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        # Return empty list if JSON parsing fails
        return []

# Database connection settings from environment variables
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'gametrackerV2')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

# IGDB API credentials from environment variables
IGDB_CLIENT_ID = os.getenv('IGDB_CLIENT_ID')
IGDB_CLIENT_SECRET = os.getenv('IGDB_CLIENT_SECRET')

# Get initial access token
access_token = igdb_api.get_igdb_access_token(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)
if not access_token:
    print("Failed to get initial access token. Check your IGDB credentials.")

# --- Database Connection Helper ---
def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Error as e:
        flash(f"Database connection error: {e}", "danger")
        print(f"Database connection error: {e}") # Log error as well
        return None

# --- Login Required Decorator ---
def login_required(view):
    """Decorator to ensure user is logged in."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# --- Routes ---
@app.route('/')
def index():
    # Pass login status to template
    return render_template('index.html', logged_in=('user_id' in session))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return render_template('search_results.html', games=[], logged_in=('user_id' in session))
        
    # Use cached access token
    global access_token
    if not access_token:
        access_token = igdb_api.get_igdb_access_token(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)
        if not access_token:
            flash("Failed to authenticate with IGDB API", "danger")
            return render_template('search_results.html', games=[], logged_in=('user_id' in session))
            
    game_data = igdb_api.get_igdb_games(query, IGDB_CLIENT_ID, access_token)
    if not game_data:
        flash(f"No games found for '{query}'", "info")
        return render_template('search_results.html', games=[], logged_in=('user_id' in session))
        
    return render_template('search_results.html', games=game_data, logged_in=('user_id' in session))

# --- Authentication Routes ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
            return redirect(url_for('register')) # Redirect back if DB connection failed
            
        cursor = conn.cursor()
        error = None

        # Basic validation
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required.'

        if error is None:
            try:
                # Hash password before storing
                hashed_password = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, hashed_password),
                )
                conn.commit()
            except mysql.connector.IntegrityError: # Catch potential unique constraint violations
                error = f"User {username} or email {email} is already registered."
            except Error as e:
                error = f"Database error during registration: {e}"
            else:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            finally:
                 cursor.close()
                 conn.close()

        flash(error, 'danger')

    # If GET request or registration failed, show the form
    return render_template('register.html') # We need to create this template later

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
             return redirect(url_for('login'))
             
        cursor = conn.cursor(dictionary=True) # Fetch rows as dictionaries
        error = None
        user = None

        try:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s", (username,)
            )
            user = cursor.fetchone()
        except Error as e:
             error = f"Database error during login: {e}"

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Incorrect password.'

        if error is None and user:
            # Store user data in session
            session.clear()
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            # Redirect to a library page or index after login
            return redirect(url_for('index'))
        
        flash(error, 'danger')
        cursor.close()
        conn.close()

    # If GET request or login failed, show the form
    return render_template('login.html') # We need to create this template later

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# --- Game Management Routes (To be updated) ---

@app.route('/add_game/<int:igdb_id>')
@login_required  # Protect this route
def add_game(igdb_id):
    # Use cached access token
    global access_token
    if not access_token:
        access_token = igdb_api.get_igdb_access_token(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)
        if not access_token:
            flash("Failed to authenticate with IGDB API", "danger")
            return redirect(request.referrer or url_for('index'))
    
    # Use the new add_game_to_db function from data_loader.py
    game = add_game_to_db(
        igdb_id, 
        IGDB_CLIENT_ID, 
        access_token, 
        DB_HOST, 
        DB_NAME, 
        DB_USER, 
        DB_PASSWORD
    )
    
    if not game:
        flash("Failed to add game. Could not retrieve game data from IGDB.", "danger")
        return redirect(request.referrer or url_for('index'))
    
    # Now add to user's tracked list
    connection = None
    try:
        connection = get_db_connection()
        if not connection:
            flash("Database connection error", "danger")
            return redirect(url_for('index'))
            
        cursor = connection.cursor()
        
        # Get user_id from session
        user_id = session['user_id']
        
        try:
            # Insert with default status ('Wishlist')
            cursor.execute(
                "INSERT INTO user_tracked_games (user_id, game_igdb_id) VALUES (%s, %s)",
                (user_id, igdb_id)
            )
            connection.commit()
            flash(f"Game '{game['name']}' added to your library!", "success")
        except mysql.connector.IntegrityError:
            # Game already tracked by this user
            flash(f"Game '{game['name']}' is already in your library.", "info")
        except Error as e:
            flash(f"Database error adding game to library: {e}", "danger")
            connection.rollback()  # Rollback on error
            
    except Error as e:
        flash(f"Database error: {e}", "danger")
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()

    # Redirect to library page after adding
    return redirect(url_for('my_library'))

# Placeholder for my_library route
@app.route('/my_library')
@login_required
def my_library():
    """Displays the games tracked by the current user."""
    user_id = session['user_id']
    tracked_games = []
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor(dictionary=True) # Fetch rows as dictionaries
        try:
            # Query joining user_tracked_games with local_games
            query = """
            SELECT
                lg.*,  -- Select all columns from local_games
                utg.status,
                utg.personal_rating,
                utg.date_added
            FROM user_tracked_games utg
            JOIN local_games lg ON utg.game_igdb_id = lg.igdb_id
            WHERE utg.user_id = %s
            ORDER BY utg.date_added DESC;
            """
            cursor.execute(query, (user_id,))
            tracked_games = cursor.fetchall()
        except Error as e:
            flash(f"Error fetching library: {e}", "danger")
            print(f"Error fetching library for user {user_id}: {e}") # Log error
        finally:
            cursor.close()
            conn.close()
            
    # We need to create my_library.html template next
    return render_template('my_library.html', library=tracked_games, logged_in=True)

# Add new route for updating game status
@app.route('/update_game_status/<int:igdb_id>', methods=['POST'])
@login_required
def update_game_status(igdb_id):
    """Updates the status, rating, and review of a tracked game."""
    user_id = session['user_id']
    status = request.form.get('status')
    rating = request.form.get('rating')
    review = request.form.get('review')
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Update the user's tracked game entry
            query = """
            UPDATE user_tracked_games 
            SET status = %s, personal_rating = %s, review = %s
            WHERE user_id = %s AND game_igdb_id = %s
            """
            cursor.execute(query, (status, rating, review, user_id, igdb_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                flash("Game status updated successfully!", "success")
            else:
                flash("No changes were made or game not found.", "warning")
                
        except Error as e:
            conn.rollback()
            flash(f"Error updating game: {e}", "danger")
            print(f"Error updating game status for user {user_id}, game {igdb_id}: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('my_library'))

# Add new route for removing a game from library
@app.route('/remove_game/<int:igdb_id>', methods=['POST'])
@login_required
def remove_game(igdb_id):
    """Removes a game from the user's tracked games."""
    user_id = session['user_id']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Delete the user's tracked game entry
            query = """
            DELETE FROM user_tracked_games
            WHERE user_id = %s AND game_igdb_id = %s
            """
            cursor.execute(query, (user_id, igdb_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                flash("Game removed from your library.", "success")
            else:
                flash("Game not found in your library.", "warning")
                
        except Error as e:
            conn.rollback()
            flash(f"Error removing game: {e}", "danger")
            print(f"Error removing game for user {user_id}, game {igdb_id}: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('my_library'))

# Add new route for viewing game details
@app.route('/game/<int:igdb_id>')
@login_required
def game_details(igdb_id):
    """Display detailed information about a specific game."""
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "danger")
        return redirect(url_for('my_library'))
    
    cursor = conn.cursor(dictionary=True)
    user_id = session['user_id']
    game_data = None
    user_data = None
    
    try:
        # Get game data from local_games table
        game_query = """
        SELECT * FROM local_games
        WHERE igdb_id = %s
        """
        cursor.execute(game_query, (igdb_id,))
        game_data = cursor.fetchone()
        
        if not game_data:
            flash("Game not found in database", "warning")
            return redirect(url_for('my_library'))
            
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
        
        # Get user-specific data for this game
        user_query = """
        SELECT status, personal_rating, review, date_added 
        FROM user_tracked_games
        WHERE user_id = %s AND game_igdb_id = %s
        """
        cursor.execute(user_query, (user_id, igdb_id))
        user_data = cursor.fetchone()
        
    except Error as e:
        flash(f"Error retrieving game details: {e}", "danger")
        print(f"Error retrieving game details for game {igdb_id}: {e}")
    finally:
        cursor.close()
        conn.close()
    
    # Pass game data and user data to the template
    return render_template('game_details.html', 
                          game=game_data, 
                          user_data=user_data,
                          logged_in=True)

if __name__ == '__main__':
    # debug=True is helpful for development but should be False in production
    app.run(debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true')