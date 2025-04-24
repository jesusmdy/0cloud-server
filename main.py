from flask import Flask, jsonify
from flask_cors import CORS
from routes import api_bp
from database import init_db

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

# Initialize database
init_db()

# Register blueprints
app.register_blueprint(api_bp)

@app.errorhandler(Exception)
def handle_error(error):
    """Handle all errors and ensure CORS headers are set."""
    response = jsonify({'error': str(error)})
    response.status_code = getattr(error, 'code', 500)
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

if __name__ == '__main__':
    app.run(debug=True, port=8080)
  