from redis_client import REDIS_CLIENT
import uuid
from datetime import datetime

def create_folder(name: str, user_id: str, parent_id: str = None) -> dict:
    """Create a new folder."""
    folder_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    REDIS_CLIENT.hset(f"folder:{folder_id}", mapping={
        "id": folder_id,
        "name": name,
        "parent_id": parent_id,
        "created_at": created_at,
        "user_id": user_id
    })
    return {
        "id": folder_id,
        "name": name,
        "parent_id": parent_id,
        "created_at": created_at,
        "user_id": user_id
    }

def get_folder(folder_id: str) -> dict:
    """Get folder details"""
    folder = REDIS_CLIENT.hgetall(f"folder:{folder_id}")
    if folder:
        return {
            "id": folder["id"].decode("utf-8"),
            "name": folder["name"].decode("utf-8"),
            "parent_id": folder["parent_id"].decode("utf-8"),
            "created_at": folder["created_at"].decode("utf-8"),
            "user_id": folder["user_id"].decode("utf-8")
        }
    return None

def list_folders(parent_id: str = None, user_id: str = None) -> list:
    """List all folders with optional parent filtering"""
    folders = REDIS_CLIENT.keys("folder:*")
    return [get_folder(folder_id.decode("utf-8")) for folder_id in folders]

