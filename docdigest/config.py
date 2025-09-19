"""
Configuration management functionality for docdigest.
Handles loading and saving of JSON configuration files.
"""

import json
from typing import Dict


def load_config(config_path: str) -> Dict:
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to the JSON configuration file

    Returns:
        Configuration dictionary with 'directory' and 'commit' keys
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")


def save_config(config_path: str, config: Dict) -> None:
    """
    Save configuration to JSON file.

    Args:
        config_path: Path to the JSON configuration file
        config: Configuration dictionary to save
    """
    with open(config_path, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=2)
