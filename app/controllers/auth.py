from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models.user import authenticate_user, register_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form.get('email') # Use .get() to handle missing email
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Basic validation
        error = None
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        # Removed email required check

        if error is None:
            # Pass email (which might be None)
            success, error = register_user(username, email, password) 
            
            if success:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))

        flash(error, 'danger')

    # If GET request or registration failed, show the form
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user, error = authenticate_user(username, password)

        if error is None and user:
            # Store user data in session
            session.clear()
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            # Redirect to a library page or index after login
            return redirect(url_for('index'))
        
        flash(error, 'danger')

    # If GET request or login failed, show the form
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
