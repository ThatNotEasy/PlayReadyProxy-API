import configparser, json, secrets, logging, coloredlogs
from functools import wraps
from modules.logging import setup_logging
from flask import request, jsonify

API_KEY_FILE = 'APIKEY.json'

def setup_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

def load_api_keys():
    try:
        with open(API_KEY_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error("APIKEY.json file not found.")
        return []
    except json.JSONDecodeError:
        logger.error("Error decoding APIKEY.json.")
        return []

def save_api_keys(api_keys):
    with open(API_KEY_FILE, 'w') as file:
        json.dump(api_keys, file, indent=4)

def is_valid_api_key(provided_key):
    api_keys = load_api_keys()
    for entry in api_keys:
        if entry.get("apikey") == provided_key:
            return True
    return False

def generate_api_key(username):
    random_key = secrets.token_hex(16)
    new_api_key = f"{username}_{random_key}"
    api_keys = load_api_keys()
    user_found = False
    for entry in api_keys:
        if entry.get("username") == username:
            entry["apikey"] = new_api_key
            user_found = True
            break

    if not user_found:
        api_keys.append({
            "username": username,
            "apikey": new_api_key
        })
    save_api_keys(api_keys)
    return new_api_key

def apikey_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        provided_key = request.headers.get('X-API-KEY')
        if not provided_key:
            logging.error("X-API-KEY header is missing.")
            return jsonify({"responseData": "Opss! API key is missing"}), 403
        if not is_valid_api_key(provided_key):
            logging.error("Invalid X-API-KEY.")
            return jsonify({"responseData": "Opss! Invalid API key"}), 403
        return func(*args, **kwargs)
    return decorated_function