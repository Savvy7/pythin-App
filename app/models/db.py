import mysql.connector
from mysql.connector import Error
import os
from flask import flash

# Database connection settings from environment variables
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'gametrackerV2')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

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
        print(f"Database connection error: {e}") # Log error as well
        try:
            flash(f"Database connection error: {e}", "danger")
        except RuntimeError:
            # This happens when we're outside of a request context
            pass
        return None

def execute_transaction(transaction_function, *args, **kwargs):
    """
    Execute a database operation within a transaction.
    
    Args:
        transaction_function: Function that takes a connection and performs database operations
        args, kwargs: Arguments to pass to the transaction function
        
    Returns:
        The result of the transaction function, or None if an error occurred
    """
    conn = get_db_connection()
    if not conn:
        return None
        
    result = None
    try:
        # Start transaction
        conn.start_transaction()
        
        # Execute the transaction function with the connection and any arguments
        result = transaction_function(conn, *args, **kwargs)
        
        # If we get here without errors, commit the transaction
        conn.commit()
    except Error as e:
        # If an error occurs, roll back the transaction
        conn.rollback()
        print(f"Transaction error: {e}")
        try:
            flash(f"Database operation failed: {e}", "danger")
        except RuntimeError:
            # This happens when we're outside of a request context
            pass
    finally:
        # Always close the connection
        if conn.is_connected():
            conn.close()
            
    return result
