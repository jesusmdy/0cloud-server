from flask import Blueprint, request, jsonify
from database import get_file_by_id

files_bp = Blueprint('files', __name__)

@files_bp.route('/files/<file_uuid>', methods=['GET', 'OPTIONS'])
def get_file(file_uuid):
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Get file from database
        file_data = get_file_by_id(file_uuid)
        if not file_data:
            return jsonify({'error': 'File not found'}), 404
            
        # Return file metadata without the encrypted content
        return jsonify({
            'id': file_data['id'],
            'encrypted_filename': file_data['encrypted_filename'],
            'original_filename': file_data['original_filename'],
            'file_size': file_data['file_size'],
            'mime_type': file_data['mime_type'],
            'parent_id': file_data['parent_id'],
            'created_at': file_data['created_at']
        })
        
    except Exception as e:
        print(f"Error getting file: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500 