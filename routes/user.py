from flask import Blueprint, request, jsonify, g
from database import count_user_filesize
from routes.auth import require_jwt
import os

user_bp = Blueprint('user', __name__)

@user_bp.route('/user', methods=['GET'])
@require_jwt
def me():
    return jsonify({
        'user_id': g.user['user_id'],
        'email': g.user['email'],
        'display_name': g.user['display_name'],
        'storage': {
            'allocated': count_user_filesize(g.user['user_id']),
            'available': os.getenv('total_storage', 107374182400),
        }
    })
