from PIL import Image
import numpy as np
from typing import List, Tuple, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_image(image_path: str) -> Dict[str, Any]:
    """Load image file (tif or jpg). For TIFF, returns multi-band array and profile."""
    try:
        file_extension = Path(image_path).suffix.lower()

        if file_extension == '.tif':
            # Load as GeoTIFF with rasterio to preserve bands
            try:
                import rasterio
                with rasterio.open(image_path) as dataset:
                    # Read all bands
                    array = dataset.read()
                    profile = dataset.profile
                    return {'array': array, 'profile': profile}
            except ImportError:
                logger.warning("rasterio not available, falling back to PIL for TIFF")
            except Exception as e:
                logger.warning(f"Failed to load GeoTIFF with rasterio: {e}, falling back to PIL")

        # Fall back to PIL for .jpg or if rasterio fails
        image = Image.open(image_path)
        # Convert PIL to numpy array (assuming RGB or grayscale)
        array = np.array(image)
        if array.ndim == 2:
            array = array[np.newaxis, ...]  # Add band dimension
        else:
            array = array.transpose(2, 0, 1)  # (H, W, C) -> (C, H, W)
        profile = {}  # No profile for non-geospatial images
        return {'array': array, 'profile': profile}

    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found: {image_path}")
    except Exception as e:
        raise ValueError(f"Error loading image {image_path}: {e}")

def extract_polygon_coordinates(coordinates: List) -> List[Tuple[int, int]]:
    """Extract polygon coordinates from MultiPolygon structure."""
    polygon_points = []

    # Handle MultiPolygon structure: coordinates[0] contains the actual polygons
    polygons = coordinates[0] if coordinates else []

    for polygon in polygons:
        for ring in polygon:
            # Each ring is a list of [x, y] coordinate pairs
            # So ring[0] is the first coordinate pair, ring[1] is the second, etc.
            for k in range(0, len(ring), 2):
                x = int(ring[k])
                y = int(ring[k + 1])
                polygon_points.append((x, y))

    logger.debug(f"Extracted {len(polygon_points)} polygon points")
    return polygon_points

def calculate_polygon_bounds(polygon_points: List[Tuple[int, int]]) -> Tuple[int, int, int, int]:
    """Calculate bounding box from polygon points."""
    if not polygon_points:
        raise ValueError("No polygon points provided")

    xs, ys = zip(*polygon_points)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    return min_x, min_y, max_x, max_y

def extract_chip_from_image(image_data: Dict[str, Any], coordinates: List,
                           padding: int = 0) -> Dict[str, Any]:
    """Extract chip from multi-band image using polygon coordinates."""
    array = image_data['array']
    profile = image_data['profile'].copy()

    polygon_points = extract_polygon_coordinates(coordinates)
    min_x, min_y, max_x, max_y = calculate_polygon_bounds(polygon_points)

    # Add padding if specified
    height, width = array.shape[1], array.shape[2]  # Assuming (bands, height, width)
    min_x = max(0, min_x - padding)
    min_y = max(0, min_y - padding)
    max_x = min(width, max_x + padding)
    max_y = min(height, max_y + padding)

    # Extract the chip from all bands
    chip_array = array[:, min_y:max_y, min_x:max_x]

    # Update profile for the chip
    profile.update({
        'height': chip_array.shape[1],
        'width': chip_array.shape[2],
        'transform': profile['transform'] * profile['transform'].translation(min_x, min_y)
    })

    return {'array': chip_array, 'profile': profile}

def save_chip(chip_data: Dict[str, Any], output_path: str):
    """Save chip to file, preserving bands for TIFF."""
    try:
        array = chip_data['array']
        profile = chip_data['profile']

        if profile:  # Geospatial TIFF
            import rasterio
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(array)
        else:  # Fallback to PIL for non-geospatial
            from PIL import Image
            # Convert back to PIL format (assuming 3 bands or 1)
            if array.shape[0] == 1:
                img = Image.fromarray(array[0])
            elif array.shape[0] == 3:
                img = Image.fromarray(array.transpose(1, 2, 0))
            else:
                # For multi-band, save as TIFF with PIL (may not preserve all bands perfectly)
                img = Image.fromarray(array[0])  # Save first band only as fallback
            img.save(output_path)

        logger.info(f"Chip saved successfully: {output_path}")
    except Exception as e:
        raise ValueError(f"Error saving chip to {output_path}: {e}")

def get_image_extension(image_path: str) -> str:
    """Get image file extension."""
    return Path(image_path).suffix.lower()