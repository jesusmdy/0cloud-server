from redis_client import REDIS_CLIENT
import uuid
from datetime import datetime
import base64
from cryptography.fernet import Fernet
import os
from crypto.keys import generate_key_from_password

def user_exists(user_id):
    """Check if a user exists by ID."""
    return REDIS_CLIENT.hget("user:" + user_id, "id") is not None

def get_user(user_id):
    """Get user by ID."""
    user_data = REDIS_CLIENT.hgetall("user:" + user_id)
    if user_data:
        return {
            "id": user_data[b"id"].decode('utf-8'),
            "email": user_data[b"email"].decode('utf-8'),
            "display_name": user_data[b"display_name"].decode('utf-8'),
            "created_at": user_data[b"created_at"].decode('utf-8'),
            "password_hash": user_data[b"password_hash"].decode('utf-8'),
            "encrypted_private_key": user_data[b"encrypted_private_key"].decode('utf-8')
        }
    return None

def get_user_by_email(email):
    """Get user by email."""
    users = REDIS_CLIENT.scan_iter("user:*")
    for user in users:
        user_data = REDIS_CLIENT.hgetall(user)
        if user_data.get(b'email') and user_data[b'email'].decode('utf-8') == email:
            return {
                "id": user_data[b"id"].decode('utf-8'),
                "email": user_data[b"email"].decode('utf-8'),
                "display_name": user_data[b"display_name"].decode('utf-8'),
                "created_at": user_data[b"created_at"].decode('utf-8')
            }
    return None

def user_exists_by_email(email):
    """Check if a user exists by email."""
    return get_user_by_email(email) is not None


def create_user(email, password_hash, encrypted_private_key, display_name):
    """Create a new user."""
    user_id = str(uuid.uuid4())
    created_at = datetime.now()

    REDIS_CLIENT.hmset(
        "user:" + user_id,
        {
            "id": user_id,
            "email": email,
            "password_hash": password_hash,
            "encrypted_private_key": encrypted_private_key,
            "display_name": display_name,
            "created_at": created_at.isoformat()
        }
    )
    return user_id

def save_user(email: str, password: str, display_name: str, private_key: str = None) -> dict:
    """Save a new user to the database."""
    
    # Generate a unique ID for the user
    user_id = str(uuid.uuid4())
    
    # Generate a salt for the password
    salt = os.urandom(16)
    
    # Generate a key from the password
    key = generate_key_from_password(password, salt)
    
    # Use provided private key or generate a new one
    if private_key:
        try:
            # Decode the provided private key from base64
            private_key_bytes = base64.b64decode(private_key)
            # Verify it's a valid Fernet key
            Fernet(private_key_bytes)
        except Exception as e:
            raise ValueError("Invalid private key format. Must be a valid Fernet key in base64 format.")
    else:
        # Generate a new Fernet key if none provided
        private_key_bytes = Fernet.generate_key()
    
    # Encrypt the private key with the password-derived key
    f = Fernet(key)
    encrypted_private_key = f.encrypt(private_key_bytes)
    
    # Store the salt and encrypted private key
    encrypted_private_key_with_salt = base64.b64encode(salt + encrypted_private_key).decode('utf-8')
    
    # Encrypt email, password, and display name with the user's private key
    f_user = Fernet(private_key_bytes)
    encrypted_password = f_user.encrypt(password.encode())
    
    # Encode encrypted data in base64
    encrypted_password_b64 = base64.b64encode(encrypted_password).decode('utf-8')
    
    # Save user to database
    create_user(email, encrypted_password_b64, encrypted_private_key_with_salt, display_name)
    
    return {
        'id': user_id,
        'email': email,
        'display_name': display_name
    }
