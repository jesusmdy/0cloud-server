import os

# Ensure encrypted files directory exists
ENCRYPTED_FILES_DIR = 'encrypted_files'
os.makedirs(ENCRYPTED_FILES_DIR, exist_ok=True)

def save_encrypted_file(file_id: str, encrypted_content: bytes) -> str:
    """Save encrypted file to disk and return the file path."""
    file_path = os.path.join(ENCRYPTED_FILES_DIR, f"{file_id}.enc")
    with open(file_path, 'wb') as f:
        f.write(encrypted_content)
    return file_path

def get_encrypted_file(file_id: str) -> bytes:
    """Read encrypted file from disk."""
    file_path = os.path.join(ENCRYPTED_FILES_DIR, f"{file_id}.enc")
    with open(file_path, 'rb') as f:
        return f.read()

def get_encrypted_file_by_filename(filename: str) -> bytes:
    """Read encrypted file from disk."""
    file_path = os.path.join(ENCRYPTED_FILES_DIR, filename)
    with open(file_path, 'rb') as f:
        return f.read()

def delete_encrypted_file(file_id: str):
    """Delete encrypted file from disk."""
    file_path = os.path.join(ENCRYPTED_FILES_DIR, f"{file_id}.enc")
    if os.path.exists(file_path):
        os.remove(file_path)
