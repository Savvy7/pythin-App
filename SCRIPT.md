
# GameTracker Project Video Script

## PART 1: Project Overview & Database Role (3-4 minutes)

### Introduction
"Hello, I'm [Your Name], and today I'm presenting my GameTracker application. This web-based platform helps gamers organize and track their video game experiences in one centralized location."

### Project Purpose
"GameTracker solves a common problem for gamers: keeping track of games we've played, are currently playing, or want to play in the future. With the vast number of games released each year across multiple platforms, it's become increasingly difficult to manage our gaming backlog efficiently."

### Value Proposition
"The application serves as a personal game library manager that allows users to:
- Search for games using the IGDB API
- Add games to their personal library
- Track game completion status
- Rate and review games they've played
- Filter and sort their collection for better organization"

### Database Architecture & Role
"The heart of GameTracker is its MySQL database, which consists of several key tables:

1. **Users Table**: Stores user authentication information and profile data
   - Primary key: user_id
   - Stores username, email, password hash, and registration date

2. **Games Table**: Caches information about games from the IGDB API
   - Primary key: game_id 
   - Stores game title, release date, genre, platform, and cover image URL
   - This improves performance by reducing API calls for previously searched games

3. **User_Games Table**: The core relationship table that connects users with their games
   - Composite primary key of user_id and game_id
   - Stores game status (Playing, Completed, Want to Play, Abandoned)
   - Contains user-specific data like rating, review, and date added

4. **Genres and Platforms Tables**: Support tables for filtering and categorization
   - Connected to games through many-to-many relationships

The database implements ACID transactions to ensure data integrity, particularly when updating user game libraries or synchronizing with the IGDB API. Foreign key constraints maintain referential integrity across tables."

### Security & Optimization
"The database is designed with security in mind, implementing prepared statements to prevent SQL injection attacks. Password hashing ensures user credentials are stored securely.

Query optimization techniques like indexing on frequently searched columns improve performance, especially important for the search functionality and library filtering operations."

## PART 2: Project Demonstration (3-4 minutes)

### User Registration & Authentication
"Let me start by demonstrating the user authentication system. New users can register with an email and password, while returning users can log in securely to access their personal library."

[DEMONSTRATE: User login process]

### Game Search Functionality
"Once logged in, users can search for games using the search bar. This leverages the IGDB API to retrieve comprehensive game information."

[DEMONSTRATE: Searching for a popular game]

"As you can see, search results display game titles, release years, platforms, and cover images. The responsive design ensures this works well on both desktop and mobile devices."

### Adding Games to Library
"Users can add games to their library with a single click. Let me add this game to my collection."

[DEMONSTRATE: Adding a game to library]

"When adding a game, users can set its status, such as 'Want to Play' or 'Currently Playing'."

### Library Management
"Now let's look at my library. Here, I can see all my games organized in a clean interface."

[DEMONSTRATE: Navigating to My Library]

"The library includes powerful filtering and sorting options. I can filter by status, sort by title or rating, and search within my collection."

[DEMONSTRATE: Filtering and sorting]

### Game Details & Editing
"For each game in my library, I can quickly update its status or rating using the pencil icon, which opens this convenient popup editor."

[DEMONSTRATE: Editing a game's status and rating]

"For games I've completed, I can add my personal review and rating to remember my experience."

### Responsive Design
"As you can see, the interface is fully responsive and adapts to different screen sizes, making it convenient to use on both desktop and mobile devices."

[DEMONSTRATE: Responsiveness if possible]

### Technical Implementation Highlights
"Behind the scenes, this application uses:
- Flask for the backend framework
- MySQL for data persistence
- IGDB API integration for game data
- Modern HTML5, CSS3, and JavaScript for the frontend
- RESTful principles for the API design"

### Conclusion
"GameTracker demonstrates the power of combining a well-designed database with an intuitive user interface to create a practical tool for gamers. The MySQL database provides robust data storage while the Flask application delivers a responsive user experience.

Future enhancements could include social features, game recommendation algorithms, and expanded statistics about gaming habits.

Thank you for watching this demonstration of my GameTracker project."
