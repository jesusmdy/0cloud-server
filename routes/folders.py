from flask import Blueprint, request, jsonify, g
from controllers.token import TokenController
from controllers.folder import FolderController
from controllers.file import FileController

folders_bp = Blueprint('folders', __name__)

@folders_bp.route('/folders', methods=['POST'])
@TokenController.require_jwt
def create_folder_route():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': FolderController.Errors.MISSING_REQUIRED_FIELD}), 400
            
        if 'name' not in data:
            return jsonify({'error': FolderController.Errors.MISSING_REQUIRED_FIELD}), 400
            
        name = data['name']
        parent_id = data.get('parent_id')
        
        folder_data = FolderController.create_folder(
            name=name,
            user_id=g.user['user_id'],
            parent_id=parent_id
        )
        
        return jsonify(folder_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@folders_bp.route('/folders', methods=['GET'])
@TokenController.require_jwt
def list_folders_route():
    try:
        parent_id = request.args.get('parent_id')
        
        folders = FolderController.list_all_folders(user_id=g.user['user_id'])
        return jsonify({'folders': folders})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@folders_bp.route('/folders/<folder_id>', methods=['GET', 'OPTIONS'])
@TokenController.require_jwt
def get_folder_route(folder_id):
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        folder = FolderController.get_folder(folder_id, g.user['user_id'])
        if not folder:
            return jsonify({'error': FolderController.Errors.FOLDER_NOT_FOUND}), 404
            
        if folder['user_id'] != g.user['user_id']:
            return jsonify({'error': FolderController.Errors.UNAUTHORIZED_ACCESS}), 403
            
        return jsonify(folder)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@folders_bp.route('/folders/<folder_id>/contents', methods=['GET'])
@TokenController.require_jwt
def list_contents(folder_id):
    try:
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
                'folders': FolderController.list_folders(None, user_id=g.user['user_id'])
            })
            
        folder = FolderController.get_folder(folder_id, g.user['user_id'])
        if not folder:
            return jsonify({'error': FolderController.Errors.FOLDER_NOT_FOUND}), 404
            
        parent = None
        if folder['parent_id']:
            parent = FolderController.get_folder(folder['parent_id'], g.user['user_id'])
            
        files = FileController.Database.list_files(parent_id=folder_id, user_id=g.user['user_id'])
        folders = FolderController.list_folders(parent_id=folder_id, user_id=g.user['user_id'])
        
        return jsonify({
            'folder': folder,
            'parent': parent,
            'files': files,
            'folders': folders
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@folders_bp.route('/folders/<folder_id>', methods=['DELETE'])
@TokenController.require_jwt
def delete_folder(folder_id):
    try:
        folder = FolderController.get_folder(folder_id, g.user['user_id'])
        if not folder:
            return jsonify({'error': FolderController.Errors.FOLDER_NOT_FOUND}), 404
        
        if folder['user_id'] != g.user['user_id']:
            return jsonify({'error': FolderController.Errors.UNAUTHORIZED_ACCESS}), 403
        
        def delete_folder_contents(folder_id):
            files = FileController.Database.list_files(parent_id=folder_id, user_id=g.user['user_id'])
            folders = FolderController.list_folders(parent_id=folder_id, user_id=g.user['user_id'])
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
