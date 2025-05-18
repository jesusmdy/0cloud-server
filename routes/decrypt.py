from flask import Blueprint, request, jsonify, g
from rdb.files import get_file_by_id, get_file_thumbs
from crypto.token import require_jwt
from controllers.file import FileController

decrypt_bp = Blueprint('decrypt', __name__)

class FileDecriptionErrors:
    FILE_NOT_FOUND = 'File not found'
    UNAUTHORIZED_ACCESS = 'Unauthorized access to file'
    NO_PRIVATE_KEY = 'No private key found in token'
    DECRYPTION_FAILED = 'Decryption failed'

@decrypt_bp.route('/folders/<parent_id>/files/<file_id>', methods=['GET'])
@require_jwt
def get_file(parent_id, file_id):
    if not FileController.Validations.is_file_owner(file_id, g.user['user_id'], parent_id):
        return jsonify({'error': FileController.Errors.UNAUTHORIZED_ACCESS}), 403
    
    file = get_file_by_id(file_id, g.user['user_id'], parent_id)
    return jsonify(file)

@decrypt_bp.route('/folders/<parent_id>/files/<file_id>/decrypt', methods=['POST'])
@require_jwt
def decrypt_file(parent_id, file_id):
    if not FileController.Validations.is_file_owner(file_id, g.user['user_id'], parent_id):
        return jsonify({'error': FileController.Errors.UNAUTHORIZED_ACCESS}), 403
    file = get_file_by_id(file_id, g.user['user_id'], parent_id)

    if not file:
        return jsonify({'error': FileController.Errors.FILE_NOT_FOUND}), 404

    private_key = g.user.get('private_key')
    if not private_key:
        return jsonify({'error': FileController.Errors.NO_PRIVATE_KEY}), 401
    
    try:
        encrypted_content = FileController.Storage.get_encrypted_file(file_id)
    except Exception as e:
        print(e)
        return jsonify({'error': FileController.Errors.FILE_NOT_FOUND}), 404

    try:
        decrypted_content = FileController.Storage.decrypt_file_content(encrypted_content, private_key)
    except Exception as e:
        print(e)
        return jsonify({'error': FileController.Errors.DECRYPTION_FAILED}), 400

    try:
        decrypted_base64 = FileController.Encoders.encode_base64(decrypted_content)
    except Exception as e:
        return jsonify({'error': FileController.Errors.DECRYPTION_FAILED}), 400
    
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
        return jsonify({'error': FileController.Errors.NO_PRIVATE_KEY}), 401

    selected_thumb = thumbs[size]
    
    print(selected_thumb, "selected_thumb")
    
    encrypted_content = FileController.Storage.get_encrypted_file_by_filename(selected_thumb['encrypted_filename'])
    if not encrypted_content:
        return jsonify({'error': FileController.Errors.FILE_NOT_FOUND}), 404
    
    try:
        decrypted_content = FileController.Storage.decrypt_file_content(encrypted_content, private_key)
    except Exception as e:
        print(e)
        return jsonify({'error': FileController.Errors.DECRYPTION_FAILED}), 400
    
    try:
        decrypted_base64 = FileController.Encoders.encode_base64(decrypted_content)
    except Exception as e:
        return jsonify({'error': FileController.Errors.DECRYPTION_FAILED}), 500
    
    return f"data:{selected_thumb['mime_type']};base64,{decrypted_base64}"