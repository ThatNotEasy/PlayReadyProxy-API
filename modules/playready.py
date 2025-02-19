import requests, base64, logging, coloredlogs, re
import xml.dom.minidom as Dom
import xml.etree.ElementTree as ET
import json

from flask import jsonify
from pathlib import Path
from modules.logging import setup_logging
from modules.config import setup_config

from pyplayready.system.pssh import PSSH
from pyplayready.device import Device
from pyplayready.cdm import Cdm
from pyplayready.exceptions import InvalidSession, InvalidLicense

class PLAYREADY:
    _instance = None  # Singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PLAYREADY, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.pssh = None
        self.challenge = None
        self.license = None
        self.session_id = None
        
        self.config = setup_config()
        self.logging = setup_logging()
        self.device_path = self.config["CDM"]["DEVICE_FILE"]
        self.device_name = self.config["CDM"]["DEVICE_NAME"]
        self.device = Device.load(Path(self.device_path))
        self.store_session = {}

# ============================================================================================================================== #

    def open_devices(self):
        if self.device_name in self.store_session:
            existing_session_id = self.store_session[self.device_name]["session_id"]
            self.logging.info(f"Existing session for {self.device_name}: {existing_session_id}")
            return jsonify({
                "responseData": {
                    "session_id": existing_session_id,
                    "device_name": self.device_name,
                    "security_level": self.store_session[self.device_name]["cdm"].security_level
                }
            }), 200

        cdm = Cdm.from_device(self.device)
        session_id = cdm.open().hex()
        self.store_session[self.device_name] = {"cdm": cdm, "session_id": session_id}
        self.logging.info(f"CDM Session Opened: {session_id}")
        return jsonify({
            "responseData": {
                "session_id": session_id,
                "device_name": self.device_name,
                "security_level": cdm.security_level
            }
        }), 200

# ============================================================================================================================== #

    def close_devices(self, session_id):
        session_id_str = session_id.decode() if isinstance(session_id, bytes) else session_id
        if self.device_name not in self.store_session:
            self.logging.error(f"No active session for device {self.device_name}.")
            return jsonify({"responseData": {"message": "No active session for this device."}}), 400

        stored_session = self.store_session[self.device_name]
        if session_id_str != stored_session["session_id"]:
            self.logging.error(f"Session mismatch: Expected {stored_session['session_id']}, got {session_id_str}")
            return jsonify({"responseData": {"message": "Invalid Session ID :P"}}), 404

        try:
            stored_session["cdm"].close(bytes.fromhex(session_id_str))
            self.logging.info(f"CDM Session Closed: {session_id_str}")

            del self.store_session[self.device_name]
            return jsonify({"responseData": {"message": f"Session {session_id_str} closed successfully."}}), 200

        except InvalidSession:
            self.logging.error(f"Invalid session ID: {session_id_str}")
            return jsonify({"responseData": {"message": "Invalid Session ID, it may have expired."}}), 400

        except Exception as e:
            self.logging.error(f"Error closing session: {str(e)}")
            return jsonify({"responseData": {"message": "Unexpected error while closing session."}}), 500
        
# ============================================================================================================================== #

    def get_challenges(self, device):
        session_entry = self.store_session.get(device)
        if not session_entry or "cdm" not in session_entry:
            return jsonify({"responseData": {"message": f"No Cdm session for {device} has been opened yet. No session to use."}}), 400
        
        cdm = session_entry["cdm"]

        try:
            session_id = bytes.fromhex(self.session_id)
        except ValueError:
            return jsonify({"responseData": {"message": "Invalid session_id format."}}), 400

        if not self.pssh.startswith("<WRMHEADER"):
            try:
                pssh = PSSH(self.pssh)
                if pssh.wrm_headers:
                    self.pssh = pssh.wrm_headers[0]
            except InvalidPssh as e:
                return jsonify({"responseData": {"message": f"Unable to parse base64 PSSH, {e}"}}), 500

        try:
            license_request = cdm.get_license_challenge(session_id=session_id,wrm_header=self.pssh)
        except InvalidSession:
            return jsonify({"responseData": {"message": f"Invalid Session ID '{session_id.hex()}', it may have expired."}}), 400
        except Exception as e:
            return jsonify({"responseData": {"message": f"Error, {e}"}}), 500

        response_data = {"challenge_b64": base64.b64encode(license_request.encode() if isinstance(license_request, str) else license_request).decode()}
        return jsonify({"responseData": response_data}), 200

# ============================================================================================================================== #

    def get_keys(self, device):
        session_entry = self.store_session.get(device)
        if not session_entry or "cdm" not in session_entry:
            return jsonify({"responseData": {"message": f"No Cdm session for {device} has been opened yet. No session to use."}}), 400

        cdm = session_entry["cdm"]
        try:
            session_id = bytes.fromhex(self.session_id)
        except ValueError:
            return jsonify({"responseData": {"message": "Invalid session_id format."}}), 400

        if not isinstance(self.license, str) or not self.license.strip():
            return jsonify({"responseData": {"message": "Invalid or empty license_message."}}), 400

        try:
            self.logging.info(f"Parsing license for session {session_id.hex()} on device {device}")
            decoded_license = base64.b64decode(self.license).decode("utf-8", errors="ignore")
            cdm.parse_license(session_id, decoded_license)
            keys = cdm.get_keys(session_id)
            response_keys = [
                {
                    "kid": key.key_id.hex,
                    "key": key.key.hex(),
                }
                for key in keys
            ]

        except InvalidSession:
            return jsonify({"responseData": {"message": f"Invalid Session ID '{session_id.hex()}', it may have expired."}}), 400
        except InvalidLicense as e:
            return jsonify({"responseData": {"message": f"Invalid License, {e}"}}), 400
        except Exception as e:
            return jsonify({"responseData": {"message": f"Error, {e}"}}), 500

        return jsonify({
            "responseData": {
                "message": "Successfully parsed and loaded the Keys from the License message.",
                "keys": response_keys
            }
        }), 200
    
# ============================================================================================================================== #
        
        

