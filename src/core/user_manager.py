import json
import os
from typing import List

# Path to the file that stores the authorized user IDs
AUTHORIZED_USERS_FILE = "src/data/authorized_users.json"

def load_authorized_users() -> List[int]:
    """
    Loads the list of authorized user IDs from the file.
    Returns an empty list if the file does not exist.
    """
    if not os.path.exists(AUTHORIZED_USERS_FILE):
        return []
    with open(AUTHORIZED_USERS_FILE, "r") as f:
        return json.load(f)

def save_authorized_users(user_ids: List[int]):
    """
    Saves the list of authorized user IDs to the file.
    """
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(AUTHORIZED_USERS_FILE), exist_ok=True)
    with open(AUTHORIZED_USERS_FILE, "w") as f:
        json.dump(user_ids, f, indent=4)

def add_authorized_user(user_id: int):
    """
    Adds a new user ID to the list of authorized users.
    """
    user_ids = load_authorized_users()
    if user_id not in user_ids:
        user_ids.append(user_id)
        save_authorized_users(user_ids)

def is_user_authorized(user_id: int) -> bool:
    """
    Checks if a user ID is in the list of authorized users.
    """
    return user_id in load_authorized_users()
