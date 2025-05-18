from flask import Blueprint, jsonify, g
from controllers.file import FileController
from controllers.token import TokenController
from controllers.user import UserController
import os

user_bp = Blueprint('user', __name__)

@user_bp.route('/user', methods=['GET'])
@TokenController.require_jwt
def me():
    try:

        token_user_id = g.user['user_id']

        user = UserController.Get.by_id(token_user_id)

        return jsonify({
            'user_id': user['id'],
            'id': user['id'],
            'email': user['email'],
            'display_name': user['display_name'],
            'storage': {
                'allocated': FileController.Database.count_user_filesize(user['id']),
                'available': os.getenv('total_storage', 107374182400),
            }
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': 'Internal error'}), 500
