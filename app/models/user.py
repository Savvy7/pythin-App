from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash
from app.models.db import get_db_connection

def get_user_by_username(username):
    """Get user by username."""
    conn = get_db_connection()
    if not conn:
        return None
        
    cursor = conn.cursor(dictionary=True)
    user = None
    
    try:
        cursor.execute(
            "SELECT * FROM users WHERE username = %s", (username,)
        )
        user = cursor.fetchone()
    except Error as e:
        print(f"Database error during user lookup: {e}")
    finally:
        cursor.close()
        conn.close()
        
    return user

def authenticate_user(username, password):
    """Authenticate a user with username and password."""
    user = get_user_by_username(username)
    
    if user is None:
        return None, "Incorrect username."
    
    if not check_password_hash(user['password_hash'], password):
        return None, "Incorrect password."
        
    return user, None

def register_user(username, email, password):
    """Register a new user."""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection error."
        
    cursor = conn.cursor()
    error = None
    success = False

    try:
        # Hash password before storing
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, hashed_password),
        )
        conn.commit()
        success = True
    except Error as e:
        if "Duplicate entry" in str(e):
            error = f"User {username} or email {email} is already registered."
        else:
            error = f"Database error during registration: {e}"
    finally:
        cursor.close()
        conn.close()

    return success, error
