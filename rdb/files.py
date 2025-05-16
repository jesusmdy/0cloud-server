from redis_client import REDIS_CLIENT


def save_file(encrypted_filename: str, original_filename: str, encrypted_content: bytes, file_size: int, user_id: str, parent_id: str = None, mime_type: str = 'application/octet-stream') -> dict:
    """Save a file to the database and encrypted content to disk."""

    # Generate a UUID for the file
    file_id = str(uuid.uuid4())

    # Get current timestamp
    created_at = datetime.utcnow().isoformat()

    # Save encrypted content to disk
    save_encrypted_file(file_id, encrypted_content)

    # Save file to Redis
    REDIS_CLIENT.hmset(
        f"file:{file_id}",
        {
            "encrypted_filename": encrypted_filename,
            "original_filename": original_filename,
            "file_size": file_size,
            "parent_id": parent_id,
            "created_at": created_at,
            "mime_type": mime_type,
            "user_id": user_id
        }
    )

    # Get the created file data
    file_data = REDIS_CLIENT.hgetall(f"file:{file_id}")

    return {
        "id": file_id,
        "encrypted_filename": file_data["encrypted_filename"].decode(),
        "original_filename": file_data["original_filename"].decode(),
        "file_size": int(file_data["file_size"]),
        "parent_id": file_data["parent_id"].decode() if file_data["parent_id"] else None,
        "created_at": file_data["created_at"].decode(),
        "mime_type": file_data["mime_type"].decode(),
        "user_id": file_data["user_id"].decode()
    }

def get_file(encrypted_filename):
    """Get file from database"""
    file_data = REDIS_CLIENT.hgetall(f"file:{encrypted_filename}")
    if file_data:
        return {
            "id": file_data["id"].decode(),
            "encrypted_filename": file_data["encrypted_filename"].decode(),
            "original_filename": file_data["original_filename"].decode(),
            "file_size": int(file_data["file_size"]),
            "parent_id": file_data["parent_id"].decode() if file_data["parent_id"] else None,
            "created_at": file_data["created_at"].decode(),
            "mime_type": file_data["mime_type"].decode(),
            "user_id": file_data["user_id"].decode()
        }
    return None

def get_file_by_id(file_id):
    """Get file from database by its ID and read encrypted content from disk."""
    file_data = REDIS_CLIENT.hgetall(f"file:{file_id}")
    if file_data:
        return {
            "id": file_data["id"].decode(),
            "encrypted_filename": file_data["encrypted_filename"].decode(),
            "original_filename": file_data["original_filename"].decode(),
            "file_size": int(file_data["file_size"]),
            "parent_id": file_data["parent_id"].decode() if file_data["parent_id"] else None,
            "created_at": file_data["created_at"].decode(),
            "mime_type": file_data["mime_type"].decode(),
            "user_id": file_data["user_id"].decode(),
            "encrypted_content": get_encrypted_file(file_id)
        }
    return None

def delete_file(file_id):
    """Delete file from database and encrypted content from disk."""
    REDIS_CLIENT.delete(f"file:{file_id}")
    delete_encrypted_file(file_id)

def count_user_filesize(user_id):
    """Count the total size of all files for a user from database."""
    file_size_sum = 0
    for file_data in REDIS_CLIENT.scan_iter(f"file:*"):
        file_data = REDIS_CLIENT.hgetall(file_data)
        if file_data["user_id"].decode() == user_id:
            file_size_sum += int(file_data["file_size"])
    return file_size_sum
