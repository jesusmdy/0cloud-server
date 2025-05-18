from flask import jsonify
from werkzeug.datastructures import FileStorage
from controllers.file import FileController
from redis_client import REDIS_CLIENT
from storage.files import delete_encrypted_file
from rdb.folders import get_folder
from utils.transformations import redis_to_dict
from crypto.files import generate_encrypted_thumbnails
import json
import mimetypes

def save_file(
    file: FileStorage,
    user_id: str,
    parent_id: str,
    file_content: bytes,
    private_key: str = None
) -> dict:
    """Save a file to the database and encrypted content to disk."""
    file_id = FileController.Utils.generate_file_id()
    
    original_filename = file.filename
    encrypted_filename = f"{file_id}.enc"
    file_size = len(file_content)
    
    mime_type, _ = mimetypes.guess_type(original_filename)
    if not mime_type:
        mime_type = 'application/octet-stream'

    encrypted_content = FileController.Storage.encrypt_file_content(file_content, private_key)
    
    if mime_type.startswith('image'):
        thumbnails = generate_encrypted_thumbnails(file_content, private_key)
    else:
        thumbnails = None

    created_at = FileController.Utils.generate_file_creation_date()

    if parent_id:
        parent_folder = get_folder(parent_id, user_id)
        if not parent_folder:
            raise Exception(f"Parent folder {parent_id} does not exist for user {user_id}.")
    else:
        parent_id = "root"

    FileController.Storage.save_encrypted_file(file_id, encrypted_content)

    try:
        saved_file = FileController.Database.save_file(
            encrypted_filename,
            original_filename,
            file_size,
            user_id,
            parent_id,
            mime_type,
            file_id,
            created_at
        )
        if thumbnails:
            FileController.Database.save_thumbnails(thumbnails, file_id, user_id)
    except Exception as e:
        print(f"Error saving file to Redis: {str(e)}")
        return None

    return saved_file

def get_file(file_hash):
    file = REDIS_CLIENT.hgetall(file_hash)
    if not file:
        return None
    t_file = redis_to_dict(file)
    return t_file

def get_file_by_id(file_id: str, user_id: str, parent_id: str = 'root'):
    """Get file from database by its ID and read encrypted content from disk."""

    file = REDIS_CLIENT.hgetall(f"user:{user_id}:files:{parent_id}:{file_id}")
    if not file:
        return None
    t_file = redis_to_dict(file)
    return t_file

def delete_file(file_id: str, user_id: str, parent_id: str = 'root'):
    """Delete file from database and encrypted content from disk."""
    REDIS_CLIENT.delete(f"user:{user_id}:files:{parent_id}:{file_id}")
    delete_encrypted_file(file_id)

def count_user_filesize(user_id: str):
    """Count the total size of all files for a user from database."""
    files = REDIS_CLIENT.keys(f"user:{user_id}:files:*")
    file_size_sum = 0
    for file in files:
        file_data = get_file(file)
        file_size_sum += int(file_data["file_size"])
    return file_size_sum

def get_file_thumbs(file_id: str, user_id: str):
    """Get file thumbnails from database"""
    thumbs =redis_to_dict(REDIS_CLIENT.hgetall(f"user:{user_id}:thumbnails:{file_id}"))
    
    for key, value in thumbs.items():
        thumbs[key] = json.loads(value)
    
    return thumbs

def list_files(parent_id: str = None, user_id: str = None, private_key: str = None):
    """List all files with optional parent folder filtering"""
    files = REDIS_CLIENT.keys(f"user:{user_id}:files:{parent_id or 'root'}:*")
    files_list = []

    for file in files:
        data = get_file(file)
        
        thumbs = get_file_thumbs(data['id'], user_id)
        
        data['thumbnails'] = thumbs
        files_list.append(data)
    
    return files_list

def list_all_files(user_id: str):
    """List all files from database"""
    files = REDIS_CLIENT.keys(f"user:{user_id}:files:*")
    files_list = []
    for file in files:
        data = get_file_by_id(file, user_id, parent_id)
        files_list.append(data)
    return files_list

