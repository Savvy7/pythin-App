from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import json
import functools # For login_required decorator
import os # To generate secret key
import igdb_api
from data_loader import add_game_to_db

app = Flask(__name__)

# Secret key for session management - Replace with a strong, random key in production
# You can generate one using: python -c 'import os; print(os.urandom(24))'
app.secret_key = os.urandom(24)

# MySQL connection settings (Consider moving to a config file or environment variables)
host_name = 'localhost'
db_name = 'gametrackerV2'
user_name = 'root'
user_password = 'password'

# IGDB API credentials
client_id = "5z3ofm5nmm44s4y4fwtidim7pp9vig"
client_secret = "xvlwctmsktbu6vz6gwwd2n6w0um4ow"

# Get initial access token
access_token = igdb_api.get_igdb_access_token(client_id, client_secret)
if not access_token:
    print("Failed to get initial access token. Check your IGDB credentials.")

# --- Database Connection Helper ---
def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = mysql.connector.connect(
            host=host_name,
            database=db_name,
            user=user_name,
            password=user_password
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
        access_token = igdb_api.get_igdb_access_token(client_id, client_secret)
        if not access_token:
            flash("Failed to authenticate with IGDB API", "danger")
            return render_template('search_results.html', games=[], logged_in=('user_id' in session))
            
    game_data = igdb_api.get_igdb_games(query, client_id, access_token)
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
        access_token = igdb_api.get_igdb_access_token(client_id, client_secret)
        if not access_token:
            flash("Failed to authenticate with IGDB API", "danger")
            return redirect(request.referrer or url_for('index'))
    
    # Use the new add_game_to_db function from data_loader.py
    game = add_game_to_db(
        igdb_id, 
        client_id, 
        access_token, 
        host_name, 
        db_name, 
        user_name, 
        user_password
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


if __name__ == '__main__':
    # debug=True is helpful for development but should be False in production
    app.run(debug=True)