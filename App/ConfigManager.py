
import json
import os
from datetime import datetime
import hashlib
from cryptography.fernet import Fernet
import base64
import getpass
import anthropic
import logging

class ConfigManager:
    def __init__(self, configFile):
        self.client = None
        self.config_file = configFile

    def generate_key_from_password(self, password: str) -> bytes:
        """Generate encryption key from password using SHA-256"""
        password_bytes = password.encode('utf-8')
        sha_hash = hashlib.sha256(password_bytes).digest()
        # Convert to Fernet-compatible key (32 bytes base64 encoded)
        return base64.urlsafe_b64encode(sha_hash)
    
    def encrypt_config(self, config_data: dict, password: str) -> None:
        """Encrypt and save configuration"""
        try:
            key = self.generate_key_from_password(password)
            cipher = Fernet(key)
            
            config_json = json.dumps(config_data).encode('utf-8')
            encrypted_data = cipher.encrypt(config_json)
            
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            
            logging.info("Configuration saved successfully")
        except Exception as e:
            logging.error(f"Failed to encrypt config: {e}")
            raise
    
    def decrypt_config(self, password: str) -> dict:
        """Decrypt and load configuration"""
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError("Config file not found")
            
            key = self.generate_key_from_password(password)
            cipher = Fernet(key)
            
            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = cipher.decrypt(encrypted_data)
            config = json.loads(decrypted_data.decode('utf-8'))
            
            logging.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logging.error(f"Failed to decrypt config: {e}")
            raise
    
    def create_config(self) -> None:
        """Create new encrypted configuration"""
        print("\n=== Create New Configuration ===")
        api_key = input("Enter your Anthropic API key: ")
        password = getpass.getpass("Enter password to encrypt config: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            print("Passwords don't match!")
            return
        
        config = {
            "anthropic_api_key": api_key,
            "created_at": datetime.now().isoformat()
        }
        
        self.encrypt_config(config, password)
        print("Configuration created and encrypted successfully!")
    
    def load_config(self) -> bool:
        """Load configuration and initialize API client"""
        try:
            if not os.path.exists(self.config_file):
                print("No configuration file found. Please create one first.")
                return False
            
            password = getpass.getpass("Enter password to decrypt config: ")
            config = self.decrypt_config(password)
            
            # Initialize Anthropic client
            self.client = anthropic.Anthropic(api_key=config["anthropic_api_key"])

            print(self.client.models.list(limit=20))
            
            return True
        except Exception as e:
            print(f"Failed to load configuration: {e}")
            return False
