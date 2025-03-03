from flask import Blueprint, request, jsonify
from flask_cors import cross_origin, CORS
from modules.config import apikey_required
from modules.playready import PLAYREADY
from modules.logging import setup_logging

# ============================================================================================================================== #

logging = setup_logging()
playready_bp = Blueprint('playready_bp', __name__)
CORS(playready_bp, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers=["Content-Type", "X-API-KEY"])

# ============================================================================================================================== #

@playready_bp.route("/<device>/open", methods=["GET"])
@apikey_required
@cross_origin()
def open_device(device):
    playready = PLAYREADY()
    if playready.device_name != device:
        response_data = {"message": "Ops! Invalid Device :P"}
        return jsonify({"responseData": response_data}), 404
    return playready.open_devices()

# ============================================================================================================================== #

@playready_bp.route("/<device>/close/<session_id>", methods=["GET"])
@apikey_required
@cross_origin()
def close_device(device, session_id):
    playready = PLAYREADY()
    if playready.device_name != device:
        response_data = {"message": "Ops! Invalid Device :P"}
        return jsonify({"responseData": response_data}), 404
    return playready.close_devices(session_id)

# ============================================================================================================================== #

@playready_bp.route("/<device>/get_challenge", methods=["POST"])
@apikey_required
@cross_origin()
def get_challenge(device):
    playready = PLAYREADY()

    if playready.device_name != device:
        return jsonify({"responseData": {"message": "Ops! Invalid Device :P"}}), 404

    data = request.get_json()
    pssh = data.get("pssh")
    session_id = data.get("session_id")

    if not pssh or not session_id:
        return jsonify({"responseData": {"message": "Missing required fields in JSON body."}}), 400

    # Verify that the session exists in store_session
    if device not in playready.store_session:
        return jsonify({"responseData": {"message": f"No active session for device {device}."}}), 400
        
    stored_session = playready.store_session[device]
    if session_id != stored_session["session_id"]:
        return jsonify({"responseData": {"message": f"Invalid session ID: {session_id}"}}), 400

    playready.pssh = pssh
    playready.session_id = session_id
    return playready.get_challenges(device)


# ============================================================================================================================== #

@playready_bp.route("/<device>/get_keys", methods=["POST"])
@apikey_required
@cross_origin()
def get_key(device):
    playready = PLAYREADY()
    if playready.device_name != device:
        return jsonify({"responseData": {"message": "Ops! Invalid Device :P"}}), 404

    data = request.get_json()
    license = data.get('license_b64', None)
    session_id = data.get('session_id', None)

    if not license or not session_id:
        return jsonify({"responseData": {"message": "Missing required fields in JSON body."}}), 400

    if device not in playready.store_session:
        return jsonify({"responseData": {"message": f"No active session for device {device}."}}), 400
        
    stored_session = playready.store_session[device]
    if session_id != stored_session["session_id"]:
        return jsonify({"responseData": {"message": f"Invalid session ID: {session_id}"}}), 400

    playready.license = license
    playready.session_id = session_id
    return playready.get_keys(device)

# ============================================================================================================================== #
