import logging, coloredlogs
import os
from datetime import datetime

def setup_logging():
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    current_time = datetime.now().strftime("%I-%M-%S_%p_%b-%d-%Y")
    log_filename = f'{current_time}.log'
    logs_folder = 'logs'
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)

    coloredlogs.install(level='DEBUG', fmt=log_format, humanize=True)
    log_filepath = os.path.join(logs_folder, log_filename)
    logging.basicConfig(level=logging.DEBUG, format=log_format, filename=log_filepath)
    
    return logging