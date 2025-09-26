import os
import json
import logging
from typing import Dict, List, Any
from pathlib import Path

def sanitize_class_name(class_name: str) -> str:
    """Convert class name to filesystem-safe format using underscores."""
    return class_name.replace(" ", "_").replace("-", "_")

def generate_chip_filename(class_name: str, filename: str, index: int, extension: str) -> str:
    """Generate chip filename following naming convention."""
    sanitized_class = sanitize_class_name(class_name)
    return f"{sanitized_class}-{filename}-{index}.{extension}"

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('chip_extraction.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def convert_paths_to_strings(obj: Any) -> Any:
    """Convert Path objects to strings for JSON serialization."""
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_paths_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_paths_to_strings(item) for item in obj]
    else:
        return obj

def save_processing_summary(summary: Dict[str, Any], output_folder: str):
    """Save processing summary to JSON file."""
    summary_file = Path(output_folder) / "processing_summary.json"
    # Convert Path objects to strings for JSON serialization
    serializable_summary = convert_paths_to_strings(summary)
    with open(summary_file, 'w') as f:
        json.dump(serializable_summary, f, indent=2)