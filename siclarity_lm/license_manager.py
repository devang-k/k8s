#!/usr/bin/env python
import os
import re
import csv
import yaml
import logging
from datetime import datetime
from cryptography.fernet import Fernet
from rich.console import Console
import uuid
from contextlib import contextmanager
import psutil 
import subprocess

logger = logging.getLogger('sivista_app')

# CSV Logging Setup
log_file = ".log.csv"
def setup_logger():
    with open(log_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ["Feature", "User", "Start", "End", "Duration", "CPU", "Mem"]
        writer.writerow(header)
    return writer

csv_logger = setup_logger()

class MonitorUsage:
    def __init__(self, feature_name, log_file=".log.csv"):
        self.feature_name = feature_name
        self.log_file = log_file
        self.start_time = None

    def start(self):
        self.start_time = datetime.now()

    def stop_and_log(self):
        end_time = datetime.now()
        duration = end_time - self.start_time
        formatted_duration = str(duration).split('.')[0]

        cpu_usage = psutil.cpu_percent()
        mem_usage = psutil.virtual_memory().percent

        log_data = [self.feature_name, os.environ.get('USER', 'unknown_user'),
                    self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    formatted_duration, cpu_usage, mem_usage]

        with open(self.log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(log_data)


def log_usage(feature, start_time, end_time, user):
    duration = end_time - start_time
    formatted_duration = str(duration).split('.')[0]
    
    cpu_usage = psutil.cpu_percent()
    mem_usage = psutil.virtual_memory().percent
    
    log_data = [feature, user, start_time.strftime("%Y-%m-%d %H:%M:%S"), 
                end_time.strftime("%Y-%m-%d %H:%M:%S"), 
                formatted_duration, cpu_usage, mem_usage]

    with open(log_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(log_data)
console = Console()

def verify_license(feature, licenses, mac_id):
    try:
        feature_license = next((item for item in licenses if item["feature_name"] == feature), None)
        if not feature_license:
            console.print(f"Feature '{feature}' is not licensed.", style="red")
            return False

        key = feature_license['encryption_key'].encode()
        token = feature_license['license_key'].encode()
        f = Fernet(key)
        decrypted_data = f.decrypt(token).decode()
        parts = decrypted_data.split(',')
        if len(parts) < 3:
            console.print(f"Invalid license format for feature '{feature}'.", style="red")
            return False

        stored_feature_name, expiration_date, stored_mac_id = parts[0], parts[1], parts[2]
        stored_mac_id = normalize_mac_address(stored_mac_id)
        mac_id = normalize_mac_address(mac_id)
        current_time = datetime.now()
        expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")

        if current_time <= expiration_date and mac_id == stored_mac_id:
            return True
        else:
            if mac_id != stored_mac_id:
                console.print("License verification failed: MAC ID does not match.", style="red")
            if current_time > expiration_date:
                console.print(f"License expired on {expiration_date.strftime('%Y-%m-%d')}. Current time: {current_time.strftime('%Y-%m-%d')}", style="red")
            return False
    except Exception as e:
        console.print(f"License verification failed: {e}", style="red")
        return False
 



def append_log(usage_log_file, master_log_file):
    try:
        # Run the 'tail' command to get the last line of usage_log.csv and append it to master_log.csv
        subprocess.run(['tail', '-n', '1', usage_log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        result = subprocess.run(['tail', '-n', '1', usage_log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        # Append the result to master_log.csv
        with open(master_log_file, 'a') as master_log:
            master_log.write(result.stdout.decode())
            
    except subprocess.CalledProcessError as e:
        logger.debug(f"Error running 'tail' command: {e}")
    except Exception as e:
        logger.debug(f"An error occurred: {e}")



@contextmanager
def use_feature(feature, licenses, mac_id, user):
    start_time = datetime.now()
    valid_license = verify_license(feature, licenses, mac_id)

    try:
        yield valid_license
    finally:
        end_time = datetime.now()
        if valid_license:
            log_usage(feature, start_time, end_time, user)


def check_license(feature_name, license_file='license.key'):
    user = os.environ.get('USER', 'unknown_user')
    current_mac_id = get_mac_id()

    try:
        with open(license_file, 'r') as f:
            licenses = yaml.safe_load(f)
            with use_feature(feature_name, licenses, current_mac_id, user) as valid_license:
                return valid_license
    except FileNotFoundError:
        console.print("License file not found.", style="red")
        return False


def get_mac_id():
    mac_id = hex(uuid.getnode())[2:].upper()
    formatted_mac_id = ':'.join(mac_id[i:i+2] for i in range(0, len(mac_id), 2)).lower()
    return formatted_mac_id

def normalize_mac_address(mac_address):
    # Remove colons and hyphens from the MAC address
    return re.sub(r'[:-]', '', mac_address).lower()

