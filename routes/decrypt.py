from flask import Blueprint, request, jsonify, g
from crypto.files import decrypt_thumbnails_list
from rdb.files import get_file_by_id, get_file_thumbs
import base64
from crypto.token import require_jwt
from cryptography.fernet import Fernet
from storage.files import get_encrypted_file, get_encrypted_file_by_filename

decrypt_bp = Blueprint('decrypt', __name__)

class FileDecriptionErrors:
    FILE_NOT_FOUND = 'File not found'
    UNAUTHORIZED_ACCESS = 'Unauthorized access to file'
    NO_PRIVATE_KEY = 'No private key found in token'
    DECRYPTION_FAILED = 'Decryption failed'

class FileOwnershipMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        return self.app(environ, start_response)
    
    def is_file_owner(file_id, user_id, parent_id):
        file = get_file_by_id(file_id, user_id, parent_id)
        return file['user_id'] == user_id

@decrypt_bp.route('/folders/<parent_id>/files/<file_id>', methods=['GET'])
@require_jwt
def get_file(parent_id, file_id):
    if not FileOwnershipMiddleware.is_file_owner(file_id, g.user['user_id'], parent_id):
        return jsonify({'error': FileDecriptionErrors.UNAUTHORIZED_ACCESS}), 403
    
    file = get_file_by_id(file_id, g.user['user_id'], parent_id)
    return jsonify(file)

@decrypt_bp.route('/folders/<parent_id>/files/<file_id>/decrypt', methods=['POST'])
@require_jwt
def decrypt_file(parent_id, file_id):
    if not FileOwnershipMiddleware.is_file_owner(file_id, g.user['user_id'], parent_id):
        return jsonify({'error': FileDecriptionErrors.UNAUTHORIZED_ACCESS}), 403
    file = get_file_by_id(file_id, g.user['user_id'], parent_id)

    if not file:
        return jsonify({'error': FileDecriptionErrors.FILE_NOT_FOUND}), 404

    private_key = g.user.get('private_key')
    if not private_key:
        return jsonify({'error': FileDecriptionErrors.NO_PRIVATE_KEY}), 401
    
    encrypted_content = get_encrypted_file(file_id)

    try:
        f = Fernet(private_key.encode())
        decrypted_content = f.decrypt(encrypted_content)
    except Exception as e:
        print(e)
        return jsonify({'error': FileDecriptionErrors.DECRYPTION_FAILED}), 400

    try:
        decrypted_base64 = base64.b64encode(decrypted_content).decode('utf-8')
    except Exception as e:
        return jsonify({'error': FileDecriptionErrors.DECRYPTION_FAILED}), 400
    
    return jsonify({
        'file': file,
        'content': decrypted_base64
    })

@decrypt_bp.route('/thumbnails/<file_id>/<size>', methods=['GET'])
@require_jwt
def get_thumbnail(file_id, size):
   thumbs = get_file_thumbs(file_id, g.user['user_id'])
   return jsonify(thumbs[size])

@decrypt_bp.route('/thumbnails/<file_id>/<size>/preview', methods=['GET'])
@require_jwt
def decrypt_thumbnail(file_id, size):
    
    thumbs = get_file_thumbs(file_id, g.user['user_id'])
    private_key = g.user.get('private_key')
    if not private_key:
        return jsonify({'error': FileDecriptionErrors.NO_PRIVATE_KEY}), 401

    selected_thumb = thumbs[size]
    
    print(selected_thumb, "selected_thumb")
    
    encrypted_content = get_encrypted_file_by_filename(selected_thumb['encrypted_filename'])
    if not encrypted_content:
        return jsonify({'error': FileDecriptionErrors.FILE_NOT_FOUND}), 404
    
    try:
        f = Fernet(private_key.encode())
        decrypted_content = f.decrypt(encrypted_content)
    except Exception as e:
        print(e)
        return jsonify({'error': f'Decryption failed: {str(e)}'}), 400
    
    try:
        decrypted_base64 = base64.b64encode(decrypted_content).decode('utf-8')
    except Exception as e:
        return jsonify({'error': f'Failed to encode decrypted content: {str(e)}'}), 500
    
    return f"data:{selected_thumb['mime_type']};base64,{decrypted_base64}"