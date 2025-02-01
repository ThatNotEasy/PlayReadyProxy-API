from flask import Flask, request, render_template, Response, jsonify
from modules.banners import banners, clear_terminal
from routes.playready import playready_bp
from flask_cors import CORS, cross_origin
from modules.config import setup_config
from modules.logging import setup_logging


banners()
logging = setup_logging()
config = setup_config()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers=["Content-Type", "X-API-KEY"])

# ========================================================================================================================================== #

prefix_url_api = '/api'
app.register_blueprint(playready_bp, url_prefix=f'{prefix_url_api}/playready')

# ========================================================================================================================================== #

@app.route('/api')
@cross_origin()
def backend_api():
    result = {"message": "Ping Pong! PlayReady Proxy API"}
    return jsonify({"responseData": result})

# ========================================================================================================================================== #

@app.route('/api/')
@cross_origin()
def backend_api_slash():
    result = {"message": "Ping Pong! PlayReady Proxy API"}
    return jsonify({"responseData": result})
    
# ========================================================================================================================================== #

if __name__ == "__main__":
    app.run()
