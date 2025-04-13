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
        
        # Handle potentially None email
        email_value = email if email else None 
        
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email_value, hashed_password),
        )
        conn.commit()
        success = True
    except Error as e:
        if "Duplicate entry" in str(e):
            # Check which field caused the duplicate error
            if f"'{username}'" in str(e) and "for key 'users.username'" in str(e):
                error = f"Username \"{username}\" is already registered."
            elif email_value and f"'{email_value}'" in str(e) and "for key 'users.email'" in str(e):
                error = f"Email \"{email_value}\" is already registered."
            else:
                 error = "Username or email is already registered." # Fallback message
        else:
            error = f"Database error during registration: {e}"
    finally:
        cursor.close()
        conn.close()

    return success, error
