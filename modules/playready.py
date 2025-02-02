import requests, base64, logging, coloredlogs, re
import xml.dom.minidom as Dom
import xml.etree.ElementTree as ET
import json

from flask import jsonify
from modules.logging import setup_logging
from modules.config import setup_config

from modules.pyplayready.pssh import PSSH
from modules.pyplayready.device import Device
from modules.pyplayready.cdm import Cdm

class PLAYREADY:
    def __init__(self):
        self.pssh = None
        self.session_id = None
        self.challenge = None
        self.license = None
        
        self.config = setup_config()
        self.device = self.config["PLAYREADY"]["DEVICE"]
        self.logging = setup_logging()

    def get_license_challenge(self):
        device = Device.load(self.device)
        cdm = Cdm.from_device(device)
        pssh = PSSH(self.pssh)
        wrm_headers = pssh.get_wrm_headers(downgrade_to_v4=False)
        raw_challenge = cdm.get_license_challenge(wrm_headers[0])
        if isinstance(raw_challenge, str):
            raw_challenge = raw_challenge.encode('utf-8')

        challenge_b64 = base64.b64encode(raw_challenge).decode('utf-8')
        return challenge_b64
    
    def get_license_keys(self):
        device = Device.load(self.device)
        cdm = Cdm.from_device(device)
        license_data = self.license
        try:
            try:
                decoded_license = base64.b64decode(license_data, validate=True).decode('utf-8', errors='replace')
            except (base64.binascii.Error, UnicodeDecodeError):
                return jsonify({"error": "License must be provided as valid Base64-encoded data"}), 400

            cleaned_license = re.sub(r'([a-zA-Z0-9:]+)(xmlns)', r'\1 \2', decoded_license)
            try:
                parsed_xml = ET.fromstring(cleaned_license)
                pretty_xml = Dom.parseString(cleaned_license).toprettyxml()
            except ET.ParseError as parse_error:
                return jsonify({"error": f"Invalid XML in license data: {parse_error}"}), 400
        except ValueError as decode_error:
            return jsonify({"error": "Invalid license format"}), 400
        try:
            cdm.parse_license(cleaned_license)
        except Exception as e:
            return jsonify({"error": f"Unable to parse license: {e}"}), 500

        try:
            key_pairs = []
            for key in cdm.get_keys():
                self.kid = key.key_id.hex() if isinstance(key.key_id, bytes) else str(key.key_id).replace("-", "")
                self.key = key.key.hex() if isinstance(key.key, bytes) else str(key.key)
                key_pairs.append({"key_id": self.kid, "key": self.key})
                print(key_pairs)
            return jsonify(key_pairs)

        except Exception as e:
            return jsonify({"error": f"Unable to extract keys: {e}"}), 500
