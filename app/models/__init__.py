from app.models.db import get_db_connection
from app.models.game import (
    search_local_games, get_all_games, get_game_details,
    get_user_game_data, add_game_to_user_library, 
    update_game_status, remove_game_from_library,
    get_user_library, get_user_library_game_ids
)
from app.models.user import (
    get_user_by_username, authenticate_user, register_user
)
