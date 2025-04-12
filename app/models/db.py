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
