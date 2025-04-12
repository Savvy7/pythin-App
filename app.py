from app import create_app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # debug=True is helpful for development but should be False in production
    app.run(debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true')