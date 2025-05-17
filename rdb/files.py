from redis_client import REDIS_CLIENT
import uuid
from datetime import datetime
from storage.files import save_encrypted_file
from storage.files import get_encrypted_file
from storage.files import delete_encrypted_file
from rdb.folders import get_folder
from utils.transformations import redis_to_dict

def save_file(
    encrypted_filename: str,
    original_filename: str,
    encrypted_content: bytes,
    file_size: int,
    user_id: str,
    parent_id: str,
    mime_type: str = 'application/octet-stream'
) -> dict:
    """Save a file to the database and encrypted content to disk."""

    # Generate a UUID for the file
    file_id = str(uuid.uuid4())

    # Get current timestamp
    created_at = datetime.now()

    if parent_id:
        parent_folder = get_folder(parent_id, user_id)
        if not parent_folder:
            raise Exception(f"Parent folder {parent_id} does not exist for user {user_id}.")
    else:
        parent_id = "root"

    # Save encrypted content to disk
    save_encrypted_file(file_id, encrypted_content)

    # Save file to Redis
    try:
        REDIS_CLIENT.hmset(
        f"user:{user_id}:files:{parent_id}:{file_id}",
        {
            "id": file_id,
            "encrypted_filename": encrypted_filename,
            "original_filename": original_filename,
            "file_size": file_size,
            "parent_id": parent_id,
            "created_at": created_at.isoformat(),
            "mime_type": mime_type,
            "user_id": user_id
        }
    )
    except Exception as e:
        print(f"Error saving file to Redis: {str(e)}")
        return None

    # Get the created file data
    # file_data = REDIS_CLIENT.hgetall(f"file:{file_id}")

    return {
        "id": file_id,
        "encrypted_filename": encrypted_filename,
        "original_filename": original_filename,
        "file_size": file_size,
        "parent_id": parent_id,
        "created_at": created_at.isoformat(),
        "mime_type": mime_type,
        "user_id": user_id
    }

def get_file(encrypted_filename):
    """Get file from database"""
    file_data = REDIS_CLIENT.hgetall(f"user:{user_id}:file:{encrypted_filename}")
    if file_data:
        return {
            "id": file_data["id"],
            "encrypted_filename": file_data["encrypted_filename"],
            "original_filename": file_data["original_filename"],
            "file_size": int(file_data["file_size"]),
            "parent_id": file_data["parent_id"],
            "created_at": file_data["created_at"],
            "mime_type": file_data["mime_type"],
            "user_id": file_data["user_id"]
        }
    return None

def get_file_by_id(file_id):
    """Get file from database by its ID and read encrypted content from disk."""
    return redis_to_dict(REDIS_CLIENT.hgetall(file_id))

def delete_file(file_id):
    """Delete file from database and encrypted content from disk."""
    REDIS_CLIENT.delete(f"user:{user_id}:file:{file_id}")
    delete_encrypted_file(file_id)

def count_user_filesize(user_id):
    """Count the total size of all files for a user from database."""
    files = REDIS_CLIENT.keys(f"user:{user_id}:file:*")
    file_size_sum = 0
    for file in files:
        file_data = REDIS_CLIENT.hgetall(file)
        file_size_sum += int(file_data["file_size"])
    return file_size_sum

def list_files(parent_id=None, user_id=None):
    """List all files with optional parent folder filtering"""
    files = REDIS_CLIENT.keys(f"user:{user_id}:files:{parent_id or 'root'}:*")
    files_list = []

    for file in files:
        data = get_file_by_id(file)
        files_list.append(data)
    
    return files_list

def list_all_files(user_id):
    """List all files from database"""
    files = REDIS_CLIENT.keys(f"user:{user_id}:file:*")
    files_list = []
    for file in files:
        data = get_file_by_id(file)
        files_list.append(data)
    return files_list

