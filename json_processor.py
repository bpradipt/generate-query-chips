import json
from typing import Dict, List, Tuple, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_json_file(json_path: str) -> Dict[str, Any]:
    """Load and validate JSON file."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {json_path}: {e}")

def extract_multipolygon_data(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract MultiPolygon data from GeoJSON FeatureCollection."""
    if json_data.get('type') != 'FeatureCollection':
        raise ValueError("JSON data is not a FeatureCollection")

    features = json_data.get('features', [])
    if not features:
        logger.warning("No features found in JSON file")
        return []

    multipolygon_data = []
    for i, feature in enumerate(features):
        if feature.get('type') != 'Feature':
            logger.warning(f"Feature {i} is not a valid Feature type")
            continue

        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})

        if geometry.get('type') != 'MultiPolygon':
            logger.warning(f"Feature {i} geometry is not MultiPolygon")
            continue

        coordinates = geometry.get('coordinates', [])
        if not coordinates:
            logger.warning(f"Feature {i} has no coordinates")
            continue

        class_name = properties.get('Class Name', 'Unknown')

        multipolygon_data.append({
            'class_name': class_name,
            'coordinates': coordinates,
            'feature_index': i
        })

    return multipolygon_data

def validate_json_structure(json_path: str) -> Tuple[bool, str]:
    """Validate JSON file structure and return status."""
    try:
        data = load_json_file(json_path)
        features = extract_multipolygon_data(data)

        if not features:
            return False, "No valid MultiPolygon features found"

        return True, f"Found {len(features)} valid MultiPolygon features"

    except Exception as e:
        return False, f"Validation error: {str(e)}"