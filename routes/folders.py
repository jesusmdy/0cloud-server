from flask import Blueprint, request, jsonify, g
from rdb.files import list_files, list_all_files
from rdb.folders import get_folder, list_folders, create_folder, list_all_folders
from crypto.token import require_jwt
from controllers.folder import Folder
from controllers.file import FileController

folders_bp = Blueprint('folders', __name__)

class FolderError:
    FOLDER_NOT_FOUND = 'Folder not found'
    UNAUTHORIZED_ACCESS = 'Unauthorized access to folder'
    MISSING_REQUIRED_FIELD = 'Missing required field'

@folders_bp.route('/folders', methods=['POST'])
@require_jwt
def create_folder_route():
    try:
        # Get JSON payload
        data = request.get_json()
        
        if not data:
            return jsonify({'error': FolderError.MISSING_REQUIRED_FIELD}), 400
            
        # Validate required fields
        if 'name' not in data:
            return jsonify({'error': FolderError.MISSING_REQUIRED_FIELD}), 400
            
        name = data['name']
        parent_id = data.get('parent_id')  # Optional
        
        # Create the folder with the user's ID from the JWT token
        folder_data = Folder.create_folder(
            name=name,
            user_id=g.user['user_id'],
            parent_id=parent_id
        )
        
        return jsonify(folder_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@folders_bp.route('/folders', methods=['GET'])
@require_jwt
def list_folders_route():
    try:
        # Get parent_id from query parameters
        parent_id = request.args.get('parent_id')
        
        # List folders for the current user
        folders = list_all_folders(user_id=g.user['user_id'])
        return jsonify({'folders': folders})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@folders_bp.route('/folders/<folder_id>', methods=['GET', 'OPTIONS'])
@require_jwt
def get_folder_route(folder_id):
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        folder = get_folder(folder_id, g.user['user_id'])
        if not folder:
            return jsonify({'error': FolderError.FOLDER_NOT_FOUND}), 404
            
        # Check if the folder belongs to the user
        if folder['user_id'] != g.user['user_id']:
            return jsonify({'error': FolderError.UNAUTHORIZED_ACCESS}), 403
            
        return jsonify(folder)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@folders_bp.route('/folders/<folder_id>/contents', methods=['GET'])
@require_jwt
def list_contents(folder_id):
    try:
        # Handle root folder (folder_id = 0)
        if folder_id == '0':
            return jsonify({
                'folder': {
                    'id': '0',
                    'name': 'root',
                    'parent_id': None,
                    'created_at': None,
                    'user_id': g.user['user_id']
                },
                'parent': None,
                'files': FileController.Database.list_files(user_id=g.user['user_id']),
                'folders': Folder.list_folders(None, user_id=g.user['user_id'])
            })
            
        # Get folder details
        folder = get_folder(folder_id, g.user['user_id'])
        if not folder:
            return jsonify({'error': 'Folder not found'}), 404
            
        # Get parent folder if exists
        parent = None
        if folder['parent_id']:
            parent = get_folder(folder['parent_id'], g.user['user_id'])
            
        # Get files and folders in this folder for the current user
        files = FileController.Database.list_files(parent_id=folder_id, user_id=g.user['user_id'])
        folders = Folder.list_folders(parent_id=folder_id, user_id=g.user['user_id'])
        
        return jsonify({
            'folder': folder,
            'parent': parent,
            'files': files,
            'folders': folders
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@folders_bp.route('/folders/<folder_id>', methods=['DELETE'])
@require_jwt
def delete_folder(folder_id):
    try:
        folder = get_folder(folder_id)
        if not folder:
            return jsonify({'error': 'Folder not found'}), 404
        
        # Check if the folder belongs to the user
        if folder['user_id'] != g.user['user_id']:
            return jsonify({'error': FolderError.UNAUTHORIZED_ACCESS}), 403
        
        def delete_folder_contents(folder_id):
            """Delete all files and folders in the given folder."""
            files = FileController.Database.list_files(parent_id=folder_id, user_id=g.user['user_id'])
            folders = Folder.list_folders(parent_id=folder_id, user_id=g.user['user_id'])
            for file in files:
                delete_file(file['id'])
            for folder in folders:
                delete_folder_contents(folder['id'])
                delete_folder(folder['id'])
        
        delete_folder_contents(folder_id)
        delete_file(folder_id)
        
        return '', 204
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
