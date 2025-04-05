from flask import Flask
from flask_cors import CORS
from routes import api_bp
from database import init_db

app = Flask(__name__)
CORS(app)

# Initialize database
init_db()

# Register blueprints
app.register_blueprint(api_bp)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
  