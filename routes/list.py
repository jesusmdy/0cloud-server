from flask import Blueprint, request, jsonify
from database import list_files

list_bp = Blueprint('list', __name__)

@list_bp.route('/files/list', methods=['GET', 'OPTIONS'])
def list():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Get query parameters
        search_term = request.args.get('search', '')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)
        parent_id = request.args.get('parent_id', type=int)
        
        # Get files from database
        result = list_files(
            search_term=search_term,
            limit=limit,
            offset=offset,
            parent_id=parent_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"List error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500 