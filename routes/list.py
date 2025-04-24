from flask import Blueprint, request, jsonify, g
from database import list_files
from routes.auth import require_jwt

list_bp = Blueprint('list', __name__)

@list_bp.route('/files/list', methods=['GET', 'OPTIONS'])
@require_jwt
def list():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Get query parameters
        search_term = request.args.get('search', '')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)
        parent_id = request.args.get('parent_id')
        
        # Get files from database for current user
        result = list_files(
            search_term=search_term,
            limit=limit,
            offset=offset,
            parent_id=parent_id,
            user_id=g.user['user_id']  # Add current user's ID
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"List error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500 