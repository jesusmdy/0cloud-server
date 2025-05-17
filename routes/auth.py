from flask import Blueprint, request, jsonify, g
from rdb.user import user_exists_by_email, get_user_by_email, get_user, save_user
from crypto.keys import generate_key_from_password
from crypto.token import create_jwt_token, verify_jwt_token
import base64
from cryptography.fernet import Fernet

auth_bp = Blueprint('auth', __name__)

class LoginError:
    INVALID_EMAIL_OR_PASSWORD = 'Invalid email or password'
    EMAIL_ALREADY_REGISTERED = 'Email already registered'
    MISSING_REQUIRED_FIELD = 'Missing required field'
    SERVER_ERROR = 'Server error'

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        # Get JSON payload
        data = request.get_json()
        
        if not data:
            return jsonify({'error': LoginError.MISSING_REQUIRED_FIELD}), 400
            
        # Validate required fields
        required_fields = ['email', 'password', 'display_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': LoginError.MISSING_REQUIRED_FIELD}), 400
                
        email = data['email']
        password = data['password']
        display_name = data['display_name']
        private_key = data.get('private_key')  # Optional field
        
        # Check if email already exists by trying to decrypt all emails
        if user_exists_by_email(email):
            return jsonify({'error': LoginError.EMAIL_ALREADY_REGISTERED}), 400
        
        # Save user and get response
        user_data = save_user(email, password, display_name, private_key)
        
        return jsonify(user_data)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Registration error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
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
        login_user = get_user_by_email(email)

        if not login_user:
            return jsonify({'error': LoginError.INVALID_EMAIL_OR_PASSWORD}), 401
        
        user_data = get_user(login_user['id'])
        user_email = user_data['email']
        password_hash = user_data['password_hash']
        private_key = user_data['encrypted_private_key']
        
        try:
            salt_and_encrypted = base64.b64decode(private_key)
            salt = salt_and_encrypted[:16]
            encrypted_private_key = salt_and_encrypted[16:]
            
            key = generate_key_from_password(password, salt)
            f = Fernet(key)
            private_key_bytes = f.decrypt(encrypted_private_key)
            
            f_user = Fernet(private_key_bytes)
            stored_password = f_user.decrypt(base64.b64decode(password_hash)).decode()
            
            if stored_password == password and user_email == email:
                token = create_jwt_token(
                    user_id=user_data['id'],
                    email=user_email,
                    display_name=user_data['display_name'],
                    private_key=private_key_bytes.decode()  # Include private key in token
                )
                return jsonify({
                    'token': token,
                    'user': {
                        'id': user_data['id'],
                        'email': user_email,
                        'display_name': user_data['display_name']
                    }
                })
        except Exception as e:
            print(f"Login error: {str(e)}")  # Debug print
            return jsonify({'error': LoginError.SERVER_ERROR}), 500
        
    except Exception as e:
        print(f"Login error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500 