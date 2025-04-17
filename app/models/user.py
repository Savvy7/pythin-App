from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash
from app.models.db import get_db_connection, execute_transaction

def get_user_by_username(username):
    """Get user by username."""
    def transaction(conn, username):
        cursor = conn.cursor(dictionary=True)
        user = None
        
        try:
            # Use a prepared statement for security
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
        finally:
            cursor.close()
            
        return user
        
    return execute_transaction(transaction, username)

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
    def transaction(conn, username, email, password):
        cursor = conn.cursor()
        error = None
        success = False

        try:
            # Hash password before storing
            hashed_password = generate_password_hash(password)
            
            # Handle potentially None email
            email_value = email if email else None 
            
            # Use prepared statement for security
            query = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
            cursor.execute(query, (username, email_value, hashed_password))
            
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
                
            # Re-raise the error to trigger a rollback
            raise
        finally:
            cursor.close()

        return success, error
    
    try:
        return execute_transaction(transaction, username, email, password)
    except Error:
        # If an error occurred in the transaction, return failure
        return False, "Registration failed. Please try again."
