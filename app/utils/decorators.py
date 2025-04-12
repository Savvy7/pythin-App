import functools
from flask import session, redirect, url_for, flash

def login_required(view):
    """Decorator to ensure user is logged in."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view
