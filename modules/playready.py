import requests, base64, coloredlogs, re, uuid
import xml.dom.minidom as Dom
import xml.etree.ElementTree as ET

from flask import jsonify
from pathlib import Path
from modules.logging import setup_logging
from modules.config import setup_config

from pyplayready.system.pssh import PSSH
from pyplayready.device import Device
from pyplayready.cdm import Cdm
from pyplayready.exceptions import InvalidSession, InvalidLicense, InvalidPssh

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
            response_data = {
            "session_id": existing_session_id,
            "device_name": self.device_name,
            "security_level": self.store_session[self.device_name]["cdm"].security_level
            }
            return jsonify({"responseData": response_data}), 200

        cdm = Cdm.from_device(self.device)
        session_id = cdm.open().hex()
        self.store_session[self.device_name] = {"cdm": cdm, "session_id": session_id}
        response_data = {
            "session_id": session_id,
            "device_name": self.device_name,
            "security_level": cdm.security_level
            }
        return jsonify({"responseData": response_data}), 200


# ============================================================================================================================== #

    def close_devices(self, session_id):
        session_id_str = session_id.decode() if isinstance(session_id, bytes) else session_id
        if self.device_name not in self.store_session:
            return jsonify({"responseData": {"message": "No active session for this device."}}), 400

        stored_session = self.store_session[self.device_name]
        if session_id_str != stored_session["session_id"]:
            return jsonify({"responseData": {"message": "Invalid Session ID :P"}}), 404

        try:
            stored_session["cdm"].close(bytes.fromhex(session_id_str))
            del self.store_session[self.device_name]
            return jsonify({"responseData": {"message": f"Session {session_id_str} closed successfully."}}), 200

        except InvalidSession:
            return jsonify({"responseData": {"message": "Invalid Session ID, it may have expired."}}), 400

        except Exception:
            return jsonify({"responseData": {"message": "Unexpected error while closing session."}}), 500

        
# ============================================================================================================================== #


    def get_challenges(self, device):
        try:
            session_entry = self.store_session.get(device)
            if not session_entry or "cdm" not in session_entry:
                return jsonify({"responseData": {"message": f"No CDM session for {device} has been opened yet. No session to use."}}), 400
            
            cdm = session_entry["cdm"]
            stored_session_id = bytes.fromhex(session_entry["session_id"])

            wrm_header = None
            if self.pssh.startswith('<WRMHEADER'):
                wrm_header = self.pssh
            else:
                try:
                    pssh_bytes = base64.b64decode(self.pssh)
                    decoded_str = pssh_bytes.decode('utf-16-le', errors='ignore')
                    
                    if '<WRMHEADER' in decoded_str:
                        start_idx = decoded_str.find('<WRMHEADER')
                        end_idx = decoded_str.find('</WRMHEADER>') + len('</WRMHEADER>')
                        if start_idx >= 0 and end_idx > start_idx:
                            wrm_header = decoded_str[start_idx:end_idx]
                    
                    if not wrm_header:
                        pssh = PSSH(self.pssh)
                        if pssh.wrm_headers:
                            wrm_header = pssh.wrm_headers[0]
                except Exception as e:
                    wrm_header = self.pssh
                
            if not wrm_header:
                return jsonify({"responseData": {"message": "Unable to extract a valid WRM header from PSSH"}}), 500

            try:
                license_request = cdm.get_license_challenge(session_id=stored_session_id, wrm_header=wrm_header)
                session = cdm._Cdm__sessions.get(stored_session_id)
                if session and hasattr(session, 'license_request') and session.license_request:
                    pass
                else:
                    if session:
                        session.license_request = license_request
                        session.header = wrm_header if isinstance(wrm_header, bytes) else wrm_header.encode('utf-8')
                        
            except InvalidSession as e:
                return jsonify({"responseData": {"message": f"Invalid Session ID '{stored_session_id.hex()}', it may have expired. Error: {str(e)}"}}), 400
            except Exception as e:
                return jsonify({"responseData": {"message": f"Error generating challenge: {str(e)}"}}), 500

            response_data = {"challenge_b64": base64.b64encode(license_request.encode() if isinstance(license_request, str) else license_request).decode()}
            return jsonify({"responseData": response_data}), 200
        except Exception as e:
            return jsonify({"responseData": {"message": f"Error generating challenge: {str(e)}"}}), 500



# ============================================================================================================================== #

    def get_keys(self, device):
        session_entry = self.store_session.get(device)
        if not session_entry or "cdm" not in session_entry:
            return jsonify({"responseData": {"message": f"No CDM session for {device} has been opened yet. No session to use."}}), 400

        cdm = session_entry["cdm"]
        stored_session_id = bytes.fromhex(session_entry["session_id"])
        
        if not isinstance(self.license, str) or not self.license.strip():
            return jsonify({"responseData": {"message": "Invalid or empty license_message."}}), 400

        try:
            decoded_license = base64.b64decode(self.license).decode("utf-8", errors="ignore")
            try:
                cdm.parse_license(stored_session_id, decoded_license)
            except Exception as e:
                return jsonify({"responseData": {"message": f"Error parsing license: {str(e)}"}}), 500
            
            try:
                keys = cdm.get_keys(stored_session_id)
                response_keys = []
                for key in keys:
                    if isinstance(key.key_id, uuid.UUID):
                        key_id_hex = key.key_id.hex
                    else:
                        key_id_hex = str(key.key_id)
                    
                    if isinstance(key.key, bytes):
                        key_hex = key.key.hex()
                    else:
                        key_hex = str(key.key)
                    
                    response_keys.append({
                        "key_id": key_id_hex,
                        "key": key_hex
                    })
            except Exception as e:
                return jsonify({"responseData": {"message": f"Error getting keys: {str(e)}"}}), 500

        except InvalidSession as e:
            return jsonify({"responseData": {"message": f"Invalid Session ID '{stored_session_id.hex()}', it may have expired."}}), 400
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
        
        

