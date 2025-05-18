from flask import Blueprint, request, jsonify, g
import uuid
from cryptography.fernet import Fernet
import mimetypes
from crypto.token import require_jwt
from controllers.file import FileController
encrypt_bp = Blueprint('encrypt', __name__)

@encrypt_bp.route('/folders/<folder_id>/files/add', methods=['PUT'])
@require_jwt
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
    
    
        
    try:
        # Get the file from the request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Get parent_id from request, default to None (root)
        parent_id = request.form.get('parent_id')
        
        # Generate a unique filename
        original_filename = file.filename
        encrypted_filename = f"{uuid.uuid4()}.enc"
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(original_filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Read the file content
        file_content = file.read()
        
        # Get the private key from the JWT token
        private_key = g.user.get('private_key')
        if not private_key:
            return jsonify({'error': 'No private key found in token'}), 401
            
        # Encrypt the file content using the user's private key
        f = Fernet(private_key.encode())
        encrypted_content = f.encrypt(file_content)
        
        # Save the encrypted file
        file_data = save_file(
            encrypted_filename=encrypted_filename,
            original_filename=original_filename,
            encrypted_content=encrypted_content,
            file_size=len(file_content),
            user_id=g.user['user_id'],
            parent_id=parent_id if parent_id else "",
            mime_type=mime_type
        )
        
        return jsonify({
            'id': file_data['id'],
            'encrypted_filename': file_data['encrypted_filename'],
            'original_filename': file_data['original_filename'],
            'file_size': file_data['file_size'],
            'parent_id': file_data['parent_id'],
            'created_at': file_data['created_at'],
            'mime_type': file_data['mime_type']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 