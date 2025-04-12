import json
import os

CONFIG_PATH = os.getenv('CSTORE_CONFIG_PATH', 'app/config/cstore.json')
DEFAULT_CONFIG = {
    "ae_title": "DISCO_SCP",
    "port": 11112,
    "bind_address": "0.0.0.0",
    "max_pdu_size": 116794,
    "storage_directory": "/data/dicom_storage" # Make sure this exists or is created
}

def load_cstore_config():
    """Loads C-STORE configuration, applying defaults for missing keys."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        # Ensure all keys exist, applying defaults if not
        updated_config = DEFAULT_CONFIG.copy()
        updated_config.update(config) # Overwrite defaults with loaded values
        # Optional: Perform basic validation (e.g., port is int, max_pdu is int > 0)
        if not isinstance(updated_config.get("port"), int):
            updated_config["port"] = DEFAULT_CONFIG["port"] # Or raise error
        if not isinstance(updated_config.get("max_pdu_size"), int) or updated_config["max_pdu_size"] <= 0:
             updated_config["max_pdu_size"] = DEFAULT_CONFIG["max_pdu_size"] # Or raise error
        # Ensure storage directory exists (or handle creation elsewhere)
        # Path validation is important here
        return updated_config
    except FileNotFoundError:
        print(f"Warning: Config file {CONFIG_PATH} not found. Using default config.")
        # Save default config if it doesn't exist?
        # save_cstore_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {CONFIG_PATH}. Using default config.")
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"Error loading config: {e}. Using default config.")
        return DEFAULT_CONFIG.copy()


def save_cstore_config(config_data):
    """Saves the C-STORE configuration."""
    try:
        # Optional: Add validation before saving
        if not isinstance(config_data.get("port"), int):
            raise ValueError("Port must be an integer")
        if not isinstance(config_data.get("max_pdu_size"), int) or config_data["max_pdu_size"] <= 0:
             raise ValueError("Max PDU size must be a positive integer")
        if not isinstance(config_data.get("bind_address"), str):
             raise ValueError("Bind address must be a string")
        if not isinstance(config_data.get("storage_directory"), str) or not config_data["storage_directory"]:
             raise ValueError("Storage directory must be a non-empty string")

        # Ensure the storage directory exists - crucial!
        # This might be better handled when the service starts or receives data,
        # but creating it here might also be valid depending on permissions.
        # os.makedirs(config_data["storage_directory"], exist_ok=True)

        with open(CONFIG_PATH, 'w') as f:
            json.dump(config_data, f, indent=2)
        print(f"C-STORE configuration saved to {CONFIG_PATH}")
        # **IMPORTANT**: You likely need to signal the cstore_scp service
        # to reload its configuration or restart after saving.
        # This could involve IPC, signals, or restarting the container/process.
    except Exception as e:
        print(f"Error saving config: {e}")
        raise # Re-raise the exception so the API layer knows it failed

# ... potentially other config related functions ...
