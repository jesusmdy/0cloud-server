from flask import Blueprint, request, jsonify, g
from rdb.files import count_user_filesize
from crypto.token import require_jwt
from rdb.user import get_user
import os

user_bp = Blueprint('user', __name__)

@user_bp.route('/user', methods=['GET'])
@require_jwt
def me():
    token_user_id = g.user['user_id']

    user = get_user(token_user_id)

    return jsonify({
        # TODO: remove user_id
        'user_id': user['id'],
        'id': user['id'],
        'email': user['email'],
        'display_name': user['display_name'],
        'storage': {
            'allocated': count_user_filesize(user['id']),
            'available': os.getenv('total_storage', 107374182400),
        }
    })
