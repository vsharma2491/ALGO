import json
import os
import shutil

CONFIG_FILE = 'config.json'
CONFIG_EXAMPLE_FILE = 'config.json.example'

def setup_config():
    """
    Checks for the existence of config.json and creates it from the
    example if it does not exist.
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"'{CONFIG_FILE}' not found.")
        if os.path.exists(CONFIG_EXAMPLE_FILE):
            print(f"Creating '{CONFIG_FILE}' from '{CONFIG_EXAMPLE_FILE}'.")
            shutil.copy(CONFIG_EXAMPLE_FILE, CONFIG_FILE)
            print("\n--- Configuration Needed ---")
            print(f"Please edit the '{CONFIG_FILE}' file and fill in your Flattrade API credentials and Telegram settings.")
            print("You can leave 'session_token' as null; the bot will generate it for you on the first run.")
            print("--------------------------\n")
        else:
            print(f"Error: '{CONFIG_EXAMPLE_FILE}' not found. Cannot create config file.")
            exit(1)

def update_token_in_config(token: str):
    """
    Updates the session token in the config.json file.

    Args:
        token (str): The new session token to save.
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: '{CONFIG_FILE}' not found. Cannot save session token.")
        return

    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)

        config_data['flattrade']['session_token'] = token

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)

        print("Successfully saved new session token to config.json.")

    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error updating config file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while saving the token: {e}")