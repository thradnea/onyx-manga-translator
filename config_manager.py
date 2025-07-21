
import json
import os

CONFIG_FILE = "config.json"

def save_config(config_data: dict):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=4)
        print(f"Configuration saved to {CONFIG_FILE}")
    except IOError as e:
        print(f"Error saving config: {e}")

def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading config: {e}")
        return {}