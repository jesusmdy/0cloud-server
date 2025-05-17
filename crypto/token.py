from datetime import datetime
import jwt
from file_tools import load_key
from datetime import timedelta
from functools import wraps
from flask import request, jsonify, g
from rdb.user import user_exists

JWT_SECRET = load_key()  # Load the JWT signing key
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = timedelta(days=1)  # Token expires in 1 day

def create_jwt_token(user_id: str, email: str, display_name: str, private_key: str = None) -> str:
    """Create a JWT token for the user."""
    payload = {
        'user_id': user_id,
        'email': email,
        'display_name': display_name,
        'exp': datetime.now() + JWT_EXPIRATION,
        'iat': datetime.now(),  # Issued at time
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
        token = auth_header
            
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
