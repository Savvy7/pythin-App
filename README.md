# GameTracker

A personal video game collection and tracking application that helps you manage your gaming backlog, track your progress, and discover new games.

![GameTracker Screenshot](https://via.placeholder.com/800x400?text=GameTracker+Screenshot)

## Features

- **Game Search**: Search for games using the IGDB API
- **Personal Library**: Build and organize your game collection
- **Game Tracking**: Track your gaming progress with status updates (Playing, Completed, Wishlist, Abandoned)
- **Rating System**: Rate games on a scale of 1-10
- **Game Details**: View comprehensive information about games including release dates, developers, platforms
- **Review System**: Write and save personal reviews for games you've played
- **Advanced Filtering**: Sort and filter your library by various criteria
- **Search Functionality**: Find games in your collection quickly
- **Responsive Design**: Works on desktop and mobile devices

## Technologies Used

- **Backend**:
  - Python 3.x
  - Flask (Web framework)
  - MySQL (Database)
  
- **Frontend**:
  - HTML5, CSS3, JavaScript
  - Jinja2 (Templating)
  
- **APIs**:
  - IGDB API (Game data)

## Installation

### Prerequisites

- Python 3.x
- MySQL Server
- Git

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/gametracker.git
   cd gametracker
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the MySQL database**:
   ```bash
   mysql -u root -p
   ```
   ```sql
   CREATE DATABASE gametrackerV2;
   ```

5. **Import database schema**:
   ```bash
   mysql -u root -p gametrackerV2 < schema.sql
   ```

6. **Create a .env file with your configuration**:
   ```
   # Database Configuration
   DB_HOST=localhost
   DB_NAME=gametrackerV2
   DB_USER=root
   DB_PASSWORD=your_password

   # IGDB API Configuration
   IGDB_CLIENT_ID=your_client_id
   IGDB_CLIENT_SECRET=your_client_secret

   # Flask Configuration
   FLASK_SECRET_KEY=your_secret_key
   FLASK_DEBUG=True
   ```

7. **Run the application**:
   ```bash
   python app.py
   ```

8. **Access the application**:
   Open your browser and go to `http://localhost:5000`

## Usage

### Creating an Account

1. Click on the "Register" link in the navigation bar
2. Fill in your username, email, and password
3. Click "Register" to create your account

### Searching for Games

1. Use the search bar on the homepage or in the navigation
2. Enter the name of a game you're looking for
3. Browse through the search results
4. Click "Add to Library" to add games to your collection

### Managing Your Library

1. Navigate to "My Library" in the navigation bar
2. Use the filter buttons to switch between different game statuses
3. Use the search bar to find specific games in your collection
4. Sort your games by various criteria using the dropdown menu
5. Click the edit (pencil) icon to update game status, rating, or review
6. Click the trash icon to remove a game from your library

### Viewing Game Details

1. Click the "Details" button on any game card
2. View comprehensive information about the game
3. Update your status, rating, and review from the game details page

## Project Structure

```
gametracker/
│
├── app/                    # Application package
│   ├── controllers/        # Route handlers
│   ├── models/             # Database models
│   ├── services/           # External API services
│   └── utils/              # Utility functions
│
├── static/                 # Static assets
│   ├── css/                # Stylesheets
│   └── js/                 # JavaScript files
│
├── templates/              # HTML templates
│
├── .env                    # Environment variables
├── app.py                  # Application entry point
├── data_loader.py          # Database loader utilities
├── igdb_api.py             # IGDB API integration
├── requirements.txt        # Python dependencies
├── schema.sql              # Database schema
└── README.md               # Project documentation
```

## Roadmap

- [ ] Game completion statistics and analytics
- [ ] Friend system to view others' libraries
- [ ] Game recommendations based on your library
- [ ] Import/export collection data
- [ ] Achievements and badges system
- [ ] Theme customization options

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [IGDB](https://www.igdb.com/api) for providing the comprehensive video game database API
- All open-source libraries and frameworks used in this project 