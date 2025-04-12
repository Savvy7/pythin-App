from flask import Flask
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def create_app(test_config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, 
                instance_relative_config=True,
                template_folder='../templates',
                static_folder='../static')
    
    # Configure from environment variables
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
    
    # Register blueprints
    from app.controllers import auth_bp, games_bp, library_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(games_bp)
    app.register_blueprint(library_bp)
    
    @app.route('/')
    def index():
        from flask import render_template, session
        # Pass login status to template
        return render_template('index.html', logged_in=('user_id' in session))
    
    return app
