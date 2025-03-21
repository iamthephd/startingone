import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from backend.api.routes import api_bp

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Set up secret key for sessions
app.secret_key = os.environ.get("SESSION_SECRET")

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')

# Root route
@app.route('/')
def root():
    return jsonify({"message": "API Server Running", "status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)