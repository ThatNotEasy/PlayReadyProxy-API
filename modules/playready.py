import requests, base64, coloredlogs, re
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
        try:
            session_entry = self.store_session.get(device)
            if not session_entry or "cdm" not in session_entry:
                return jsonify({"responseData": {"message": f"No Cdm session for {device} has been opened yet. No session to use."}}), 400
            
            cdm = session_entry["cdm"]
            self.logging.debug(f"[DEBUG] get_challenges - CDM stato prima: {cdm.__dict__}")

            # Usa l'ID della sessione memorizzato
            stored_session_id = bytes.fromhex(session_entry["session_id"])
            
            self.logging.debug(f"[DEBUG] get_challenges - Using stored session ID: {stored_session_id.hex()}")

            wrm_header = None
            
            # Verifica prima se il PSSH è già un WRM header
            if self.pssh.startswith('<WRMHEADER'):
                wrm_header = self.pssh
                self.logging.debug(f"[DEBUG] PSSH rilevato come WRM header diretto")
            else:
                # Prova a decodificare il PSSH base64 per vedere se contiene un WRM header
                try:
                    pssh_bytes = base64.b64decode(self.pssh)
                    decoded_str = pssh_bytes.decode('utf-16-le', errors='ignore')
                    
                    if '<WRMHEADER' in decoded_str:
                        # Estrai il WRM header dal PSSH decodificato
                        start_idx = decoded_str.find('<WRMHEADER')
                        end_idx = decoded_str.find('</WRMHEADER>') + len('</WRMHEADER>')
                        if start_idx >= 0 and end_idx > start_idx:
                            wrm_header = decoded_str[start_idx:end_idx]
                            self.logging.debug(f"[DEBUG] WRM header estratto dal PSSH decodificato")
                    
                    # Se non è stato trovato un WRM header nel contenuto decodificato, prova con l'analisi standard
                    if not wrm_header:
                        self.logging.debug(f"[DEBUG] Tentativo di analizzare PSSH come PSSH box")
                        pssh = PSSH(self.pssh)
                        if pssh.wrm_headers:
                            wrm_header = pssh.wrm_headers[0]
                            self.logging.debug(f"[DEBUG] Analisi PSSH riuscita, estratto WRM header")
                        else:
                            self.logging.debug(f"[DEBUG] Analisi PSSH riuscita, ma nessun WRM header trovato")
                except Exception as e:
                    self.logging.error(f"[ERROR] Errore nell'analisi PSSH: {str(e)}")
                    self.logging.debug(f"[DEBUG] Tentativo di usare il PSSH così com'è")
                    wrm_header = self.pssh  # Usa il PSSH così com'è come ultimo tentativo
            
            if not wrm_header:
                self.logging.error(f"[ERROR] Impossibile estrarre un WRM header valido dal PSSH")
                return jsonify({"responseData": {"message": "Unable to extract a valid WRM header from PSSH"}}), 500

            try:
                self.logging.debug(f"[DEBUG] Richiesta challenge con session_id={stored_session_id.hex()} e WRM header={wrm_header[:50]}...")
                license_request = cdm.get_license_challenge(session_id=stored_session_id, wrm_header=wrm_header)
                
                # Verifica che la richiesta di licenza sia stata memorizzata nella sessione
                session = cdm._Cdm__sessions.get(stored_session_id)
                if session and hasattr(session, 'license_request') and session.license_request:
                    self.logging.debug(f"[DEBUG] La richiesta di licenza è stata memorizzata correttamente nella sessione")
                else:
                    self.logging.error(f"[ERROR] La richiesta di licenza NON è stata memorizzata nella sessione!")
                    
                    # Tentativo di memorizzare manualmente la license_request nella sessione
                    if session:
                        self.logging.debug(f"[DEBUG] Tentativo di memorizzare manualmente la richiesta di licenza")
                        session.license_request = license_request
                        session.header = wrm_header if isinstance(wrm_header, bytes) else wrm_header.encode('utf-8')
                        self.logging.debug(f"[DEBUG] Richiesta di licenza memorizzata manualmente nella sessione")
                    
            except InvalidSession as e:
                self.logging.error(f"[ERROR] Invalid Session ID '{stored_session_id.hex()}': {str(e)}")
                return jsonify({"responseData": {"message": f"Invalid Session ID '{stored_session_id.hex()}', it may have expired. Error: {str(e)}"}}), 400
            except Exception as e:
                self.logging.error(f"[ERROR] Errore durante la generazione del challenge: {str(e)}, {type(e)}")
                import traceback
                self.logging.error(traceback.format_exc())
                return jsonify({"responseData": {"message": f"Error generating challenge: {str(e)}"}}), 500

            response_data = {"challenge_b64": base64.b64encode(license_request.encode() if isinstance(license_request, str) else license_request).decode()}
            return jsonify({"responseData": response_data}), 200
        except Exception as e:
            self.logging.error(f"[ERROR] Errore generale in get_challenges: {str(e)}")
            import traceback
            self.logging.error(traceback.format_exc())
            return jsonify({"responseData": {"message": f"Errore generale: {str(e)}"}}), 500



# ============================================================================================================================== #

    def get_keys(self, device):
        self.logging.debug(f"[DEBUG] get_keys called with device: {device}")
        session_entry = self.store_session.get(device)
        if not session_entry or "cdm" not in session_entry:
            self.logging.debug(f"[DEBUG] No CDM session found for device: {device}")
            return jsonify({"responseData": {"message": f"No Cdm session for {device} has been opened yet. No session to use."}}), 400

        cdm = session_entry["cdm"]
        
        # Controlla lo stato del CDM prima dell'operazione
        self.logging.debug(f"[DEBUG] CDM stato prima: {cdm.__dict__}")
        self.logging.debug(f"[DEBUG] Store sessions: {self.store_session}")
        
        # Usa l'ID della sessione memorizzato
        stored_session_id = bytes.fromhex(session_entry["session_id"])
        
        self.logging.debug(f"[DEBUG] Using stored session ID: {stored_session_id.hex()}")
        
        if not isinstance(self.license, str) or not self.license.strip():
            self.logging.debug("[DEBUG] Invalid or empty license_message")
            return jsonify({"responseData": {"message": "Invalid or empty license_message."}}), 400

        try:
            # Verifica se esiste una sessione e se ha una richiesta di licenza associata
            # Commentato per test
            # session = cdm._Cdm__sessions.get(stored_session_id)
            # if not session or not hasattr(session, 'license_request') or not session.license_request:
            #    self.logging.error(f"[ERROR] La sessione non ha una richiesta di licenza associata. È necessario chiamare get_challenge prima di get_keys.")
            #    return jsonify({"responseData": {"message": "È necessario effettuare prima una richiesta di licenza con get_challenge per questa sessione."}}), 400
            
            # Continuare con il tentativo di ottenere le chiavi, anche se la license_request non è stata memorizzata
            self.logging.info(f"Parsing license for session {stored_session_id.hex()} on device {device}")
            decoded_license = base64.b64decode(self.license).decode("utf-8", errors="ignore")
            self.logging.debug(f"[DEBUG] Decoded license: {decoded_license[:50]}...")
            
            try:
                cdm.parse_license(stored_session_id, decoded_license)
            except Exception as e:
                self.logging.error(f"[ERROR] Errore durante parse_license: {str(e)}")
            
            try:
                keys = cdm.get_keys(stored_session_id)
                response_keys = [
                    {
                        "key_id": key.key_id.hex,
                        "key": key.key.hex(),
                    }
                    for key in keys
                ]
                self.logging.debug(f"[DEBUG] Extracted keys: {response_keys}")
            except Exception as e:
                self.logging.error(f"[ERROR] Errore durante get_keys: {str(e)}")
                import traceback
                self.logging.error(traceback.format_exc())
                return jsonify({"responseData": {"message": f"Error getting keys: {str(e)}"}}), 500

        except InvalidSession as e:
            self.logging.debug(f"[DEBUG] Invalid Session ID '{stored_session_id.hex()}', possibly expired. Errore: {str(e)}")
            return jsonify({"responseData": {"message": f"Invalid Session ID '{stored_session_id.hex()}', it may have expired."}}), 400
        except InvalidLicense as e:
            self.logging.debug(f"[DEBUG] Invalid License: {e}")
            return jsonify({"responseData": {"message": f"Invalid License, {e}"}}), 400
        except Exception as e:
            self.logging.debug(f"[DEBUG] Unexpected error: {e}")
            return jsonify({"responseData": {"message": f"Error, {e}"}}), 500

        return jsonify({
            "responseData": {
                "message": "Successfully parsed and loaded the Keys from the License message.",
                "keys": response_keys
            }
        }), 200

    
# ============================================================================================================================== #
        
        

