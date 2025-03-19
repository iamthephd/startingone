import json
import os

CONFIG_FILE = 'app_config.json'

def load_config():
    """Load configuration from JSON file"""
    default_config = {
        'contributing_columns': ['Sales', 'Revenue'],
        'top_n': 3
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return default_config
    except Exception:
        return default_config

def save_config(config):
    """Save configuration to JSON file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Error saving config: {e}")
