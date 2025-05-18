from cryptography.fernet import Fernet
import os
import base64
from utils.transformations import redis_to_dict
from redis_client import REDIS_CLIENT
import json
from uuid import uuid4
from datetime import datetime
import mimetypes
from crypto.files import generate_encrypted_thumbnails
from werkzeug.datastructures import FileStorage
from controllers.folder import Folder
from controllers.database import Database

class FileController:
    ENCRYPTED_FILES_DIR = 'encrypted_files'
    os.makedirs(ENCRYPTED_FILES_DIR, exist_ok=True)
    
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
            parent_folder = Folder.get_folder(parent_id, user_id)
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

    class Errors:
        FILE_NOT_FOUND = 'File not found'
        UNAUTHORIZED_ACCESS = 'Unauthorized access to file'
        NO_PRIVATE_KEY = 'No private key found in token'
        DECRYPTION_FAILED = 'Decryption failed'
        
    class Storage:
        
        def save_encrypted_file(file_id: str, encrypted_content: bytes) -> str:
            """Save encrypted file to disk and return the file path."""
            file_path = os.path.join(FileController.ENCRYPTED_FILES_DIR, f"{file_id}.enc")
            with open(file_path, 'wb') as f:
                f.write(encrypted_content)
            return file_path
        
        def encrypt_file_content(
            file_content: bytes,
            private_key: str
        ):
            f = Fernet(private_key.encode())
            encrypted_content = f.encrypt(file_content)
            return encrypted_content

        def decrypt_file_content(
            encrypted_content: bytes,
            private_key: str
        ):
            try:
                f = Fernet(private_key.encode())
                decrypted_content = f.decrypt(encrypted_content)
            except Exception as e:
                return None
            return decrypted_content
        
        def get_encrypted_file(file_id: str) -> bytes:
            """Read encrypted file from disk."""
            file_path = os.path.join(FileController.ENCRYPTED_FILES_DIR, f"{file_id}.enc")
            with open(file_path, 'rb') as f:
                return f.read()
        
        def get_encrypted_file_by_filename(filename: str) -> bytes:
            """Read encrypted file from disk."""
            file_path = os.path.join(FileController.ENCRYPTED_FILES_DIR, filename)
            with open(file_path, 'rb') as f:
                return f.read()
            
        def delete_encrypted_file(file_id: str):
            """Delete encrypted file from disk."""
            file_path = os.path.join(FileController.ENCRYPTED_FILES_DIR, f"{file_id}.enc")
            if os.path.exists(file_path):
                os.remove(file_path)
    
    class Utils:
        def generate_file_id():
            return str(uuid4())
        
        def generate_file_creation_date():
            return datetime.now()
    
    class Encoders:
        def encode_base64(
            content: bytes
        ):
            return base64.b64encode(content).decode('utf-8')
    
    class Validations:
        def is_file_owner(file_id, user_id, parent_id):
            file = FileController.Database.get_file_by_id(file_id, user_id, parent_id)
            return file['user_id'] == user_id
        
    class Database:
        
        def save_file(
            encrypted_filename: str,
            original_filename: str,
            file_size: int,
            user_id: str,
            parent_id: str,
            mime_type: str = 'application/octet-stream',
            file_id: str = None,
            created_at: datetime = None
        ) -> dict:
            try:
                Database.hmset(
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
        
        def get_file_by_id(file_id: str, user_id: str, parent_id: str = 'root'):
            """Get file from database by its ID and read encrypted content from disk."""

            file = Database.hgetall(f"user:{user_id}:files:{parent_id}:{file_id}")
            if not file:
                return None
            t_file = redis_to_dict(file)
            return t_file

        def get_file(file_hash):
            file = Database.hgetall(file_hash)
            if not file:
                return None
            t_file = redis_to_dict(file)
            return t_file

        def delete_file(file_id: str, user_id: str, parent_id: str = 'root'):
            """Delete file from database and encrypted content from disk."""
            Database.delete(f"user:{user_id}:files:{parent_id}:{file_id}")
            FileController.Storage.delete_encrypted_file(file_id)
        
        def count_user_filesize(user_id: str):
            """Count the total size of all files for a user from database."""
            files = Database.keys(f"user:{user_id}:files:*")
            file_size_sum = 0
            for file in files:
                file_data = FileController.Database.get_file(file)
                file_size_sum += int(file_data["file_size"])
            return file_size_sum
        
        def get_file_thumbs(file_id: str, user_id: str):
            """Get file thumbnails from database"""
            thumbs =redis_to_dict(Database.hgetall(f"user:{user_id}:thumbnails:{file_id}"))
    
            for key, value in thumbs.items():
                thumbs[key] = json.loads(value)
    
            return thumbs
        
        def list_files(parent_id: str = None, user_id: str = None):
            """List all files with optional parent folder filtering"""
            files = Database.keys(f"user:{user_id}:files:{parent_id or 'root'}:*")
            files_list = []

            for file in files:
                data = FileController.Database.get_file(file)
        
                thumbs = FileController.Database.get_file_thumbs(data['id'], user_id)
                
                data['thumbnails'] = thumbs
                files_list.append(data)
            
            return files_list
        
        def list_all_files(user_id: str):
            """List all files from database"""
            files = Database.keys(f"user:{user_id}:files:*")
            files_list = []
            for file in files:
                data = FileController.Database.get_file_by_id(file, user_id)
                files_list.append(data)
            return files_list
        
        def save_thumbnails(thumbnails: list, file_id: str, user_id: str):
            """Save file thumbnails to database"""
            Database.hmset(
                f"user:{user_id}:thumbnails:{file_id}",
                {str(key): json.dumps(value) for key, value in thumbnails.items()}
            )
        
  