from datetime import datetime
import jwt
from flask import request, jsonify, g
from rdb.user import user_exists
from controllers.key import KeyController
from functools import wraps
from datetime import timedelta

class TokenController:
  JWT_SECRET = KeyController.Load.jwt()
  JWT_ALGORITHM = 'HS256'
  JWT_EXPIRATION = timedelta(days=1)
  
  def issue(user_id: str, email: str, display_name: str, private_key: str = None) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'display_name': display_name,
        'exp': datetime.now() + TokenController.JWT_EXPIRATION,
        'iat': datetime.now(),
        'iss': 'crypi-api'
    }
    if private_key:
        payload['private_key'] = private_key
    return jwt.encode(payload, TokenController.JWT_SECRET, algorithm=TokenController.JWT_ALGORITHM)

  def verify(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            TokenController.JWT_SECRET,
            algorithms=[TokenController.JWT_ALGORITHM],
            issuer='crypi-api'
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError as e:
        raise ValueError(f'Invalid token: {str(e)}')
      
  def require_jwt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        auth_header = request.headers.get('Authorization')
        token = auth_header
            
        if not token:
            return jsonify({'error': 'Missing token'}), 401
            
        try:
            data = TokenController.verify(token)

            if not user_exists(data['user_id']):
                return jsonify({'error': 'User not found'}), 401
                
            g.user = data
            return f(*args, **kwargs)
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
            
    return decorated_function
