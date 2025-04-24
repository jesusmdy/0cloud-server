from flask import Blueprint
from .encrypt import encrypt_bp
from .decrypt import decrypt_bp
from .list import list_bp
from .folders import folders_bp
from .files import files_bp
from .auth import auth_bp
from .user import user_bp
# Create main blueprint
api_bp = Blueprint('api', __name__)

# Register all blueprints
api_bp.register_blueprint(encrypt_bp)
api_bp.register_blueprint(decrypt_bp)
api_bp.register_blueprint(list_bp)
api_bp.register_blueprint(folders_bp)
api_bp.register_blueprint(files_bp)
api_bp.register_blueprint(auth_bp) 
api_bp.register_blueprint(user_bp)