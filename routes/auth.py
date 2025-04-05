from flask import Blueprint, request, jsonify, g
import uuid
from datetime import datetime, timedelta
import sqlite3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import jwt
from file_tools import load_key
from functools import wraps
from database import user_exists

auth_bp = Blueprint('auth', __name__)

# JWT configuration
JWT_SECRET = load_key()  # Load the JWT signing key
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = timedelta(days=1)  # Token expires in 1 day

def generate_key_from_password(password: str, salt: bytes) -> bytes:
    """Generate a key from a password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def create_jwt_token(user_id: str, email: str, display_name: str, private_key: str = None) -> str:
    """Create a JWT token for the user."""
    payload = {
        'user_id': user_id,
        'email': email,
        'display_name': display_name,
        'exp': datetime.utcnow() + JWT_EXPIRATION,
        'iat': datetime.utcnow(),  # Issued at time
        'iss': 'crypi-api'  # Issuer
    }
    if private_key:
        payload['private_key'] = private_key
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Verify a JWT token and return the payload if valid."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            issuer='crypi-api'
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError as e:
        raise ValueError(f'Invalid token: {str(e)}')

def require_jwt(f):
    """Middleware to require JWT authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
        if not token:
            return jsonify({'error': 'Missing token'}), 401
            
        try:
            # Decode the token
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            # Verify user exists in database
            if not user_exists(data['user_id']):
                return jsonify({'error': 'User not found'}), 401
                
            # Store user data in g for use in routes
            g.user = data
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
            
    return decorated_function

def save_user(email: str, password: str, display_name: str, private_key: str = None) -> dict:
    """Save a new user to the database."""
    conn = sqlite3.connect('files.db')
    c = conn.cursor()
    
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
    encrypted_email = f_user.encrypt(email.encode())
    encrypted_password = f_user.encrypt(password.encode())
    encrypted_display_name = f_user.encrypt(display_name.encode())
    
    # Encode encrypted data in base64
    encrypted_email_b64 = base64.b64encode(encrypted_email).decode('utf-8')
    encrypted_password_b64 = base64.b64encode(encrypted_password).decode('utf-8')
    encrypted_display_name_b64 = base64.b64encode(encrypted_display_name).decode('utf-8')
    
    # Save user to database
    c.execute('''
        INSERT INTO users (id, email, password_hash, encrypted_private_key, display_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, encrypted_email_b64, encrypted_password_b64, encrypted_private_key_with_salt, encrypted_display_name_b64, datetime.now()))
    
    conn.commit()
    conn.close()
    
    return {
        'id': user_id,
        'email': email,
        'display_name': display_name
    }

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Get JSON payload
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON payload provided'}), 400
            
        # Validate required fields
        required_fields = ['email', 'password', 'display_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        email = data['email']
        password = data['password']
        display_name = data['display_name']
        private_key = data.get('private_key')  # Optional field
        
        # Check if email already exists by trying to decrypt all emails
        conn = sqlite3.connect('files.db')
        c = conn.cursor()
        c.execute('SELECT id, email, encrypted_private_key FROM users')
        for row in c.fetchall():
            try:
                # Get the user's private key
                encrypted_private_key_with_salt = row[2]
                salt_and_encrypted = base64.b64decode(encrypted_private_key_with_salt)
                salt = salt_and_encrypted[:16]
                encrypted_private_key = salt_and_encrypted[16:]
                
                # Try to decrypt with the provided password
                key = generate_key_from_password(password, salt)
                f = Fernet(key)
                private_key_bytes = f.decrypt(encrypted_private_key)
                
                # Try to decrypt the email
                f_user = Fernet(private_key_bytes)
                stored_email = f_user.decrypt(base64.b64decode(row[1])).decode()
                
                if stored_email == email:
                    conn.close()
                    return jsonify({'error': 'Email already registered'}), 400
            except:
                # If decryption fails, skip this user
                continue
        conn.close()
        
        # Save user and get response
        user_data = save_user(email, password, display_name, private_key)
        
        return jsonify(user_data)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Registration error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Get JSON payload
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON payload provided'}), 400
            
        # Validate required fields
        required_fields = ['email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        email = data['email']
        password = data['password']
        
        # Try to find and authenticate the user
        conn = sqlite3.connect('files.db')
        c = conn.cursor()
        c.execute('SELECT id, email, password_hash, encrypted_private_key, display_name FROM users')
        
        for row in c.fetchall():
            try:
                # Get the user's encrypted data
                encrypted_private_key_with_salt = row[3]
                salt_and_encrypted = base64.b64decode(encrypted_private_key_with_salt)
                salt = salt_and_encrypted[:16]
                encrypted_private_key = salt_and_encrypted[16:]
                
                # Try to decrypt with the provided password
                key = generate_key_from_password(password, salt)
                f = Fernet(key)
                private_key_bytes = f.decrypt(encrypted_private_key)
                
                # Try to decrypt the email and password
                f_user = Fernet(private_key_bytes)
                stored_email = f_user.decrypt(base64.b64decode(row[1])).decode()
                stored_password = f_user.decrypt(base64.b64decode(row[2])).decode()
                stored_display_name = f_user.decrypt(base64.b64decode(row[4])).decode()
                
                # If email matches and password is correct
                if stored_email == email and stored_password == password:
                    conn.close()
                    # Create JWT token with private key
                    token = create_jwt_token(
                        user_id=row[0],
                        email=stored_email,
                        display_name=stored_display_name,
                        private_key=private_key_bytes.decode()  # Include private key in token
                    )
                    return jsonify({
                        'token': token,
                        'user': {
                            'id': row[0],
                            'email': stored_email,
                            'display_name': stored_display_name
                        }
                    })
            except:
                # If decryption fails, skip this user
                continue
                
        conn.close()
        return jsonify({'error': 'Invalid email or password'}), 401
        
    except Exception as e:
        print(f"Login error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500 