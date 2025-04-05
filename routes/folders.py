from flask import Blueprint, request, jsonify, g
from database import create_folder, get_folder, list_folders, list_files, list_all_files
from routes.auth import require_jwt

folders_bp = Blueprint('folders', __name__)

@folders_bp.route('/folders', methods=['POST', 'OPTIONS'])
@require_jwt
def create_folder_route():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Get JSON payload
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON payload provided'}), 400
            
        # Validate required fields
        if 'name' not in data:
            return jsonify({'error': 'Missing required field: name'}), 400
            
        name = data['name']
        parent_id = data.get('parent_id')  # Optional
        
        # Create the folder with the user's ID from the JWT token
        folder_data = create_folder(
            name=name,
            user_id=g.user['user_id'],
            parent_id=parent_id
        )
        
        return jsonify(folder_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@folders_bp.route('/folders', methods=['GET', 'OPTIONS'])
@require_jwt
def list_folders_route():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Get parent_id from query parameters
        parent_id = request.args.get('parent_id')
        
        # List folders for the current user
        folders = list_folders(parent_id=parent_id, user_id=g.user['user_id'])
        return jsonify({'folders': folders})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@folders_bp.route('/folders/<folder_id>', methods=['GET', 'OPTIONS'])
@require_jwt
def get_folder_route(folder_id):
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        folder = get_folder(folder_id)
        if not folder:
            return jsonify({'error': 'Folder not found'}), 404
            
        # Check if the folder belongs to the user
        if folder['user_id'] != g.user['user_id']:
            return jsonify({'error': 'Unauthorized access to folder'}), 403
            
        return jsonify(folder)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@folders_bp.route('/folders/<folder_id>/contents', methods=['GET', 'OPTIONS'])
@require_jwt
def list_contents(folder_id):
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Handle root folder (folder_id = 0)
        if folder_id == '0':
            return jsonify({
                'folder': {
                    'id': '0',
                    'name': 'root',
                    'parent_id': None,
                    'created_at': None
                },
                'parent': None,
                'files': list_files(parent_id=None, user_id=g.user['user_id'])['files'],
                'folders': list_folders(parent_id=None, user_id=g.user['user_id'])
            })
            
        # Get folder details
        folder = get_folder(folder_id)
        if not folder:
            return jsonify({'error': 'Folder not found'}), 404
            
        # Check if the folder belongs to the user
        if folder['user_id'] != g.user['user_id']:
            return jsonify({'error': 'Unauthorized access to folder'}), 403
            
        # Get parent folder if exists
        parent = None
        if folder['parent_id']:
            parent = get_folder(folder['parent_id'])
            # Check if parent folder belongs to the user
            if parent and parent['user_id'] != g.user['user_id']:
                parent = None  # Don't show parent if not owned by user
            
        # Get files and folders in this folder for the current user
        files_result = list_files(parent_id=folder_id, user_id=g.user['user_id'])
        folders = list_folders(parent_id=folder_id, user_id=g.user['user_id'])
        
        return jsonify({
            'folder': folder,
            'parent': parent,
            'files': files_result['files'],
            'folders': folders
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@folders_bp.route('/debug/files', methods=['GET'])
@require_jwt
def debug_files():
    """Debug endpoint to list all files with their user_ids."""
    try:
        files = list_all_files()
        return jsonify({
            'files': files,
            'current_user_id': g.user['user_id']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500 