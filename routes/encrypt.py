from flask import Blueprint, request, jsonify, g
from controllers.token import TokenController
from controllers.file import FileController
encrypt_bp = Blueprint('encrypt', __name__)

@encrypt_bp.route('/folders/<folder_id>/files/add', methods=['PUT'])
@TokenController.require_jwt
def add_file_to_folder(folder_id):
    if 'file' not in request.files:
        return jsonify({'error': FileController.Errors.FILE_NOT_FOUND}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': FileController.Errors.FILE_NOT_FOUND}), 400

    file_content = file.read()

    private_key = g.user.get('private_key')
    if not private_key:
        return jsonify({'error': FileController.Errors.NO_PRIVATE_KEY}), 401

    parent_id = folder_id
    if not parent_id:
        parent_id = "root"
    elif parent_id == "root":
        parent_id = None

    
    return FileController.save_file(
        file = file,
        user_id=g.user['user_id'],
        file_content=file_content,
        parent_id=parent_id,
        private_key=private_key
    )