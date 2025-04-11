import streamlit as st
import mysql.connector
from mysql.connector import Error
import json
import igdb_api
import os
from streamlit_option_menu import option_menu

# Database connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='gametrackerV2',
            user='root',
            password='password'
        )
        return conn
    except Error as e:
        st.error(f"Database connection error: {e}")
        return None

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = None

# Main app
def main():
    st.set_page_config(
        page_title="Game Tracker",
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Navigation
    with st.sidebar:
        st.title("Game Tracker")
        menu = option_menu(
            menu_title=None,
            options=["Home", "Search", "My Library", "Login/Register"],
            icons=["house", "search", "collection", "person"],
            default_index=0
        )

    if menu == "Home":
        show_home()
    elif menu == "Search":
        show_search()
    elif menu == "My Library":
        show_library()
    elif menu == "Login/Register":
        show_auth()

def show_home():
    st.header("Welcome to Game Tracker")
    st.write("Track your favorite games and discover new ones!")

def show_search():
    st.header("Search Games")
    # Search functionality will go here

def show_library():
    if not st.session_state.user_id:
        st.warning("Please login to view your library")
        return
    
    st.header("My Game Library")
    # Library display will go here

def show_auth():
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                handle_login(username, password)
    
    with tab2:
        # Registration form
        with st.form("register_form"):
            new_username = st.text_input("Username")
            email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")
            
            if submitted:
                handle_register(new_username, email, new_password, confirm_password)

def handle_login(username, password):
    # Login logic will go here
    pass

def handle_register(username, email, password, confirm_password):
    # Registration logic will go here
    pass

if __name__ == "__main__":
    main()