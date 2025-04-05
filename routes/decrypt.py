from flask import Blueprint, request, jsonify, g
from database import get_file_by_id
import base64
import traceback
import os
from cryptography.fernet import Fernet
from routes.auth import require_jwt

decrypt_bp = Blueprint('decrypt', __name__)

@decrypt_bp.route('/files/decrypt', methods=['POST', 'OPTIONS'])
@require_jwt
def decrypt():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Get JSON payload
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON payload provided'}), 400
            
        # Validate required fields
        required_fields = ['id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Get file from database
        file_id = data['id']
        file = get_file_by_id(file_id)
        
        if not file:
            return jsonify({'error': 'File not found'}), 404
            
        # Check if the file belongs to the user
        if file['user_id'] != g.user['user_id']:
            return jsonify({'error': 'Unauthorized access to file'}), 403
            
        # Get the private key from the JWT token
        private_key = g.user.get('private_key')
        if not private_key:
            return jsonify({'error': 'No private key found in token'}), 401
            
        # Decrypt the content using the user's private key
        try:
            f = Fernet(private_key.encode())
            decrypted_content = f.decrypt(file['encrypted_content'])
        except Exception as e:
            return jsonify({'error': f'Decryption failed: {str(e)}'}), 400
        
        # Convert decrypted content to base64
        try:
            decrypted_base64 = base64.b64encode(decrypted_content).decode('utf-8')
        except Exception as e:
            return jsonify({'error': f'Failed to encode decrypted content: {str(e)}'}), 500
        
        # Convert file object to be JSON serializable
        serializable_file = {
            'id': file['id'],
            'encrypted_filename': file['encrypted_filename'],
            'original_filename': file['original_filename'],
            'file_size': file['file_size'],
            'mime_type': file['mime_type'],
            'parent_id': file['parent_id'],
            'created_at': file['created_at']
        }
        
        return jsonify({
            'file': serializable_file,
            'content': decrypted_base64
        })
        
    except Exception as e:
        print(f"Decryption error: {str(e)}")  # Debug print
        print(f"Traceback: {traceback.format_exc()}")  # Print full traceback
        return jsonify({'error': str(e)}), 500