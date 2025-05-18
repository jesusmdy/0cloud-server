from redis_client import REDIS_CLIENT
import uuid
from datetime import datetime
from utils.transformations import redis_to_dict

def create_folder(name: str, user_id: str, parent_id: str = None) -> dict:
    """Create a new folder."""
    folder_id = str(uuid.uuid4())
    created_at = datetime.now()
    mapping = {
        "id": folder_id,
        "name": name,
        "parent_id": parent_id or "root",
        "created_at": created_at.isoformat(),
        "user_id": user_id
    }
    REDIS_CLIENT.hset(f"user:{user_id}:folders:{folder_id}", mapping=mapping)
    return mapping

def get_folder(folder_id: str, user_id: str) -> dict:
    """Get folder details"""
    folder = REDIS_CLIENT.hgetall(f"user:{user_id}:folders:{folder_id}")
    if folder:
        return redis_to_dict(folder)
    return None

def get_direct_folder(folder_id: str) -> dict:
    """Get folder details"""
    folder = REDIS_CLIENT.hgetall(folder_id)
    return redis_to_dict(folder)

def list_folders(parent_id: str = None, user_id: str = None) -> list:
    """List all folders with optional parent filtering"""
    folders = REDIS_CLIENT.keys(f"user:{user_id}:folders:*")

    children_folders = []

    for folder_id in folders:
        folder = get_direct_folder(folder_id)
        if (parent_id is None):
            if folder['parent_id'] == "root":
                children_folders.append(folder_id)
        if folder['parent_id'] == parent_id:
            children_folders.append(folder_id)
    return [
        get_direct_folder(folder_id) for folder_id in children_folders
    ]

def list_all_folders(user_id: str = None) -> list:
    """List all folders with optional parent filtering"""
    folders = REDIS_CLIENT.keys(f"user:{user_id}:folders:*")
    return [get_direct_folder(folder_id) for folder_id in folders]

