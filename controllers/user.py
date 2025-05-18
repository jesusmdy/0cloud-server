from controllers.database import Database
from controllers.crypto import CryptoController
from controllers.token import TokenController
from crypto.keys import generate_key_from_password
import re
import base64
from datetime import datetime

class UserController:
    
    class Errors:
        EMAIL_ALREADY_REGISTERED = 'Email already registered'
        MISSING_REQUIRED_FIELD = 'Missing required field'
        SERVER_ERROR = 'Server error'
        INVALID_EMAIL_OR_PASSWORD = 'Invalid email or password'
    
    class Auth:
        def register(
            email: str,
            password: str,
            display_name: str
        ):
            UserController.Set.prepare_user(email, password, display_name)
            return {
                'user_id': UserController.Get.by_email(email)['id'],
                'email': email,
                'display_name': display_name
            }
            
        def login(
            email: str,
            password: str
        ):
            login_user = UserController.Get.by_email(email)

            if not login_user:
                return UserController.Errors.INVALID_EMAIL_OR_PASSWORD
            
            
            user_id, user_email, display_name, _, password_hash, private_key = UserController.Get.raw_user(login_user['id'])
            
            try:
                salt_and_encrypted = CryptoController.Base64.decode(private_key)
                salt = salt_and_encrypted[:16]
                encrypted_private_key = salt_and_encrypted[16:]
                
                key = CryptoController.Password.key_from_password(password, salt)
                
                try:
                    private_key_bytes = CryptoController.Key.decrypt(encrypted_private_key, key)
                except Exception as e:
                    print("Private key decryption error: ", e)
                    return UserController.Errors.INVALID_EMAIL_OR_PASSWORD
                
                try:
                    stored_password = CryptoController.Password.decrypt(CryptoController.Base64.decode(password_hash), private_key_bytes)
                except Exception as e:
                    print("Password decrypt error ", e)
                    return UserController.Errors.INVALID_EMAIL_OR_PASSWORD
                
                if stored_password == password and user_email == email:
                    token = TokenController.issue(
                        user_id,
                        user_email,
                        display_name,
                        private_key_bytes.decode()
                    )
                    return {
                        'user_id': user_id,
                        'email': user_email,
                        'display_name': display_name,
                        'token': token
                    }
            except Exception as e:
                return UserController.Errors.INVALID_EMAIL_OR_PASSWORD
    
    class Validators:
        def validate_email(email):
            if not email:
                raise ValueError("Email is required")
            if not re.match(r"^[^@]+@[^@]+\.[^@]+", email):
                raise ValueError("Invalid email format")
            
        def validate_password(password):
            if not password:
                raise ValueError("Password is required")
            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters long")
            
        def validate_display_name(display_name):
            if not display_name:
                raise ValueError("Display name is required")
            if len(display_name) < 3:
                raise ValueError("Display name must be at least 3 characters long")
    
    class Get:
        def by_id(user_id):
            user_data = Database.hgetall(f"user:{user_id}")
            if user_data:
                return Database.Utils.to_dict(user_data)
            return None
        
        def raw_user(user_id):
            user_data = UserController.Get.by_id(user_id)
            
            if not user_data:
                return None
            
            return (
                user_data['id'],
                user_data['email'],
                user_data['display_name'],
                user_data['created_at'],
                user_data['password_hash'],
                user_data['encrypted_private_key']
            )
        
        def by_email(email):
            users = Database.keys("user:*")
            for user in users:
                user_data = Database.hgetall(user)
                if user_data.get(b'email') and user_data[b'email'].decode('utf-8') == email:
                    return Database.Utils.to_dict(user_data)
            return None
        
    class Set:
        def set_user(
            email: str,
            password_hash: str,
            encrypted_private_key: str,
            display_name: str,
            user_id: str,
            created_at: datetime
        ):
            Database.hmset(
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
        
        def prepare_user(
            email: str,
            password: str,
            display_name: str,
        ):
            UserController.Validators.validate_email(email)
            UserController.Validators.validate_password(password)
            UserController.Validators.validate_display_name(display_name)

            user_id = Database.Utils.gen_uuid()
            created_at = Database.Utils.gen_timestamp()
            
            encrypted_private_key_with_salt, password_hash = CryptoController.Misc.gen_user_crypto(password)
            
            UserController.Set.set_user(
                email,
                password_hash,
                encrypted_private_key_with_salt,
                display_name,
                user_id,
                created_at
            )
            
            return {
                'user_id': user_id,
                'email': email,
                'display_name': display_name
            }
            
        
    class Utils:
        
        def user_exists(user_id):
            return Database.exists(f"user:{user_id}")
        
        def exists_by_email(email):
            return UserController.Get.by_email(email) is not None
        
        