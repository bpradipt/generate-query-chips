from PIL import Image
import numpy as np
from typing import List, Tuple, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_image(image_path: str) -> Image.Image:
    """Load image file (tif or jpg)."""
    try:
        file_extension = Path(image_path).suffix.lower()

        if file_extension == '.tif':
            # Try to load as GeoTIFF with rasterio first
            try:
                import rasterio
                with rasterio.open(image_path) as dataset:
                    # Read the first band and convert to PIL Image
                    band = dataset.read(1)
                    # Normalize the data to 0-255 range if needed
                    if band.dtype != np.uint8:
                        band = ((band - band.min()) / (band.max() - band.min()) * 255).astype(np.uint8)
                    image = Image.fromarray(band)
                    return image
            except ImportError:
                logger.warning("rasterio not available, falling back to PIL for TIFF")
            except Exception as e:
                logger.warning(f"Failed to load GeoTIFF with rasterio: {e}, falling back to PIL")

        # Fall back to PIL for both .tif and .jpg
        image = Image.open(image_path)
        return image

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

def extract_chip_from_image(image: Image.Image, coordinates: List,
                          padding: int = 0) -> Image.Image:
    """Extract chip from image using polygon coordinates."""
    polygon_points = extract_polygon_coordinates(coordinates)
    min_x, min_y, max_x, max_y = calculate_polygon_bounds(polygon_points)

    # Add padding if specified
    min_x = max(0, min_x - padding)
    min_y = max(0, min_y - padding)
    max_x = min(image.width, max_x + padding)
    max_y = min(image.height, max_y + padding)

    # Extract the chip
    chip = image.crop((min_x, min_y, max_x, max_y))
    return chip

def save_chip(chip: Image.Image, output_path: str):
    """Save chip to file."""
    try:
        chip.save(output_path)
        logger.info(f"Chip saved successfully: {output_path}")
    except Exception as e:
        raise ValueError(f"Error saving chip to {output_path}: {e}")

def get_image_extension(image_path: str) -> str:
    """Get image file extension."""
    return Path(image_path).suffix.lower()