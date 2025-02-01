from flask import Blueprint, request, jsonify
from flask_cors import cross_origin, CORS
from modules.config import apikey_required
from modules.playready import PLAYREADY
from modules.logging import setup_logging

# Setup logging
logging = setup_logging()

playready_bp = Blueprint('playready_bp', __name__)
CORS(playready_bp, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers=["Content-Type", "X-API-KEY"])

@playready_bp.route('/extension', methods=['POST'])
@apikey_required
@cross_origin()
def extension():
    if not request.is_json:
        response_data = {"message": "Missing JSON in request."}
        return jsonify({"responseData": response_data}), 400
    
    data = request.get_json()
    action = data.get('action', None)
    
    if not action:
        response_data = {"message": "Missing action in request."}
        return jsonify({"responseData": response_data}), 400
    
    if action == "Challenge?":
        pssh = data.get('pssh', None)
    
        if not pssh:
            response_data = {"message": "Missing pssh in request."}
            return jsonify({"responseData": response_data}), 400
    
        playready = PLAYREADY()
        playready.pssh = pssh
        return playready.get_license_challenge()
    
    elif action == "Keys?":
        license = data.get('license', None)
    
        if not license:
            response_data = {"message": "Missing license in request."}
            return jsonify({"responseData": response_data}), 400
    
        playready = PLAYREADY()
        playready.license = license
        return playready.get_license_keys()
    
    else:
        response_data = {"message": "Unknown action."}
        return jsonify({"responseData": response_data}), 400