from flask import Blueprint, request, jsonify
from controllers.user import UserController

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': UserController.Errors.MISSING_REQUIRED_FIELD}), 400
            
        required_fields = ['email', 'password', 'display_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': UserController.Errors.MISSING_REQUIRED_FIELD}), 400
                
        email = data['email']
        password = data['password']
        display_name = data['display_name']
        
        if UserController.Get.by_email(email):
            return jsonify({'error': UserController.Errors.EMAIL_ALREADY_REGISTERED}), 400
        
        user_data = UserController.Auth.register(email, password, display_name)
        
        return jsonify(user_data)
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': UserController.Errors.MISSING_REQUIRED_FIELD}), 400
            
        required_fields = ['email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': UserController.Errors.MISSING_REQUIRED_FIELD}), 400
                
        email = data['email']
        password = data['password']
        try:
            return UserController.Auth.login(email, password)
        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({'error': UserController.Errors.INVALID_EMAIL_OR_PASSWORD}), 401
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500 