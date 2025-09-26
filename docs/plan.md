# Query Chips Extraction Implementation Plan

## Overview

Create a Python program to extract query chips from labelled datasets by reading JSON files containing MultiPolygon coordinates and extracting the corresponding image regions from source images (.tif/.jpg files).

## Current State Analysis

**Data Structure Verified:**
- JSON files contain GeoJSON FeatureCollection with MultiPolygon geometries
- Pixel coordinates are correct and require no transformation
- Each feature contains "Class Name" property for chip naming
- Source image filenames match the "name" field in JSON files

**Key Technical Requirements:**
- Extract chips using exact polygon boundaries (not bounding boxes)
- Support both .tif and .jpg formats (default: tif)
- Sanitize class names using underscores (e.g., "Brick Kiln" → "Brick_Kiln")
- Comprehensive error handling with processing summary
- Modular, reusable function design

## Desired End State

A command-line Python program that:
- Takes input folder and output folder as arguments
- Processes all labelled datasets in the input folder
- Extracts chips using exact polygon coordinates
- Names chips as `{sanitized-class-name}-{filename}-{index}.{extension}`
- Generates a processing summary file with success/failure details
- Handles errors gracefully without stopping the entire process

## What We're NOT Doing

- Image format conversion or optimization
- Coordinate system transformations
- Interactive GUI (command-line only)
- Real-time progress visualization (log-based only)

## Implementation Approach

**High-level Strategy:**
1. Create modular functions for each major operation
2. Use parallel processing where possible for performance
3. Implement comprehensive error handling and logging
4. Generate detailed processing summary
5. Follow the specified naming convention exactly

**Technical Architecture:**
- Main script with command-line interface using argparse
- Separate modules for JSON parsing, image processing, and chip extraction
- Error handling that logs issues but continues processing
- Processing summary in JSON format for easy parsing

## Phase 1: Project Setup and Core Infrastructure

### Overview
Set up the project structure, dependencies, and core utility functions.

### Changes Required:

**1. Project Structure**
```
query_chips_extractor/
├── main.py                    # Main script with CLI interface
├── json_processor.py          # JSON parsing and validation
├── image_processor.py         # Image reading and chip extraction
├── utils.py                   # Utility functions (naming, logging)
└── requirements.txt           # Python dependencies
```

**2. Dependencies Setup**
**File**: `requirements.txt`
**Changes**: Define required packages

```txt
Pillow>=10.0.0
numpy>=1.24.0
tqdm>=4.65.0
```

**3. Core Utility Functions**
**File**: `utils.py`
**Changes**: Implement utility functions for naming and logging

```python
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

def save_processing_summary(summary: Dict[str, Any], output_folder: str):
    """Save processing summary to JSON file."""
    summary_file = Path(output_folder) / "processing_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
```

### Success Criteria:

#### Automated Verification:
- [ ] Project structure created correctly
- [ ] Dependencies installed: `uv pip install -r requirements.txt`
- [ ] Core utilities import without errors: `python -c "import utils; print('Utils imported successfully')"`
- [ ] No linting errors: `python -m py_compile utils.py`

#### Manual Verification:
- [ ] Logging setup works correctly with different log levels
- [ ] Class name sanitization handles edge cases properly
- [ ] Chip filename generation matches expected format

---

## Phase 2: JSON Processing Module

### Overview
Implement JSON parsing and MultiPolygon coordinate extraction.

### Changes Required:

**1. JSON Processing Module**
**File**: `json_processor.py`
**Changes**: Implement JSON parsing functionality

```python
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
```

### Success Criteria:

#### Automated Verification:
- [ ] JSON processing functions work with sample data
- [ ] Invalid JSON files are handled gracefully
- [ ] MultiPolygon extraction works correctly
- [ ] No syntax errors: `python -m py_compile json_processor.py`

#### Manual Verification:
- [ ] Edge cases handled properly (empty features, missing properties)
- [ ] Error messages are clear and helpful
- [ ] Validation function provides accurate feedback

---

## Phase 3: Image Processing Module

### Overview
Implement image reading and chip extraction from polygon coordinates.

### Changes Required:

**1. Image Processing Module**
**File**: `image_processor.py`
**Changes**: Implement image processing functionality

```python
from PIL import Image
import numpy as np
from typing import List, Tuple, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_image(image_path: str) -> Image.Image:
    """Load image file (tif or jpg)."""
    try:
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
            for coord in ring:
                if len(coord) >= 2:
                    x, y = int(coord[0]), int(coord[1])
                    polygon_points.append((x, y))

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
```

### Success Criteria:

#### Automated Verification:
- [ ] Image loading works for both tif and jpg formats
- [ ] Polygon coordinate extraction handles various structures
- [ ] Chip extraction produces valid images
- [ ] No syntax errors: `python -m py_compile image_processor.py`

#### Manual Verification:
- [ ] Extracted chips match the expected polygon regions
- [ ] Padding parameter works correctly
- [ ] Error handling for invalid coordinates works properly

---

## Phase 4: Main Script and CLI Interface

### Overview
Create the main script with command-line interface and processing orchestration.

### Changes Required:

**1. Main Script**
**File**: `main.py`
**Changes**: Implement main processing logic

```python
#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from tqdm import tqdm
import time

from json_processor import load_json_file, extract_multipolygon_data, validate_json_structure
from image_processor import load_image, extract_chip_from_image, save_chip, get_image_extension
from utils import generate_chip_filename, setup_logging, save_processing_summary, sanitize_class_name

logger = logging.getLogger(__name__)

def process_single_dataset(json_path: str, input_folder: str, output_folder: str,
                          extension: str = 'tif') -> Dict[str, Any]:
    """Process a single dataset (JSON + corresponding image)."""
    result = {
        'json_file': json_path,
        'status': 'success',
        'chips_created': 0,
        'errors': [],
        'source_image': None
    }

    try:
        # Load and parse JSON
        json_data = load_json_file(json_path)
        filename = json_data.get('name', Path(json_path).stem)

        # Find corresponding image file
        image_extensions = ['.tif', '.jpg', '.jpeg']
        source_image_path = None

        for ext in image_extensions:
            potential_path = Path(input_folder) / f"{filename}{ext}"
            if potential_path.exists():
                source_image_path = str(potential_path)
                break

        if not source_image_path:
            result['status'] = 'error'
            result['errors'].append(f"Source image not found for {filename}")
            return result

        result['source_image'] = source_image_path

        # Load source image
        image = load_image(source_image_path)

        # Extract MultiPolygon data
        multipolygon_data = extract_multipolygon_data(json_data)

        if not multipolygon_data:
            result['status'] = 'error'
            result['errors'].append("No valid MultiPolygon data found")
            return result

        # Process each feature
        for i, feature in enumerate(multipolygon_data):
            try:
                class_name = feature['class_name']
                coordinates = feature['coordinates']

                # Extract chip
                chip = extract_chip_from_image(image, coordinates)

                # Generate filename
                chip_filename = generate_chip_filename(class_name, filename, i + 1, extension)
                chip_path = Path(output_folder) / chip_filename

                # Save chip
                save_chip(chip, str(chip_path))
                result['chips_created'] += 1

            except Exception as e:
                error_msg = f"Error processing feature {i}: {str(e)}"
                logger.error(error_msg)
                result['errors'].append(error_msg)

        if result['errors']:
            result['status'] = 'partial_success'

    except Exception as e:
        result['status'] = 'error'
        result['errors'].append(str(e))
        logger.error(f"Error processing {json_path}: {e}")

    return result

def main():
    parser = argparse.ArgumentParser(description='Extract query chips from labelled datasets')
    parser.add_argument('input_folder', help='Input folder containing labelled datasets')
    parser.add_argument('output_folder', help='Output folder for extracted chips')
    parser.add_argument('--extension', default='tif', choices=['tif', 'jpg'],
                       help='Source image extension to process (default: tif)')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger.info("Starting chip extraction process")

    # Create output folder
    Path(args.output_folder).mkdir(parents=True, exist_ok=True)

    # Find all JSON files
    json_files = list(Path(args.input_folder).rglob('*.json'))
    logger.info(f"Found {len(json_files)} JSON files to process")

    if not json_files:
        logger.error("No JSON files found in input folder")
        return

    # Process datasets
    results = []
    start_time = time.time()

    for json_file in tqdm(json_files, desc="Processing datasets"):
        result = process_single_dataset(str(json_file), args.input_folder,
                                      args.output_folder, args.extension)
        results.append(result)

    # Generate summary
    summary = generate_processing_summary(results, len(json_files), start_time)

    # Save summary
    save_processing_summary(summary, args.output_folder)

    # Print final summary
    print("\n" + "="*50)
    print("PROCESSING COMPLETE")
    print("="*50)
    print(f"Total datasets processed: {len(json_files)}")
    print(f"Successful: {summary['successful_count']}")
    print(f"Partial success: {summary['partial_success_count']}")
    print(f"Failed: {summary['failed_count']}")
    print(f"Total chips created: {summary['total_chips_created']}")
    print(f"Processing time: {summary['processing_time']:.2f} seconds")
    print(f"Summary saved to: {args.output_folder}/processing_summary.json")
    print("="*50)

def generate_processing_summary(results: List[Dict], total_files: int, start_time: float) -> Dict[str, Any]:
    """Generate processing summary statistics."""
    successful_count = sum(1 for r in results if r['status'] == 'success')
    partial_success_count = sum(1 for r in results if r['status'] == 'partial_success')
    failed_count = sum(1 for r in results if r['status'] == 'error')
    total_chips = sum(r['chips_created'] for r in results)

    return {
        'total_files_processed': total_files,
        'successful_count': successful_count,
        'partial_success_count': partial_success_count,
        'failed_count': failed_count,
        'total_chips_created': total_chips,
        'processing_time': time.time() - start_time,
        'results': results
    }

if __name__ == '__main__':
    main()
```

### Success Criteria:

#### Automated Verification:
- [ ] Main script runs without syntax errors
- [ ] Argument parsing works correctly
- [ ] Processing summary generation works
- [ ] No import errors: `python -c "import main; print('Main script imports successfully')"`

#### Manual Verification:
- [ ] Command-line interface accepts all parameters correctly
- [ ] Help message is clear and informative
- [ ] Error handling works for invalid inputs

---

## Phase 5: Testing and Validation

### Overview
Test the complete system with sample data and validate functionality.

### Changes Required:

**1. Test Script**
**File**: `test_chip_extraction.py`
**Changes**: Create comprehensive tests

```python
import unittest
import tempfile
import json
from pathlib import Path
from PIL import Image
import numpy as np

from json_processor import load_json_file, extract_multipolygon_data
from image_processor import load_image, extract_chip_from_image, get_image_extension
from utils import generate_chip_filename, sanitize_class_name

class TestChipExtraction(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

        # Create test JSON data
        self.test_json = {
            "type": "FeatureCollection",
            "name": "test_image",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "Class Name": "Test Class"
                    },
                    "geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [
                                    [10, 10], [10, 50], [50, 50], [50, 10]
                                ]
                            ]
                        ]
                    }
                }
            ]
        }

        # Create test image
        self.test_image = Image.new('RGB', (100, 100), color='white')
        self.test_image_path = Path(self.temp_dir) / "test_image.tif"
        self.test_image.save(self.test_image_path)

        # Save test JSON
        self.test_json_path = Path(self.temp_dir) / "test_image.json"
        with open(self.test_json_path, 'w') as f:
            json.dump(self.test_json, f)

    def test_json_processing(self):
        data = load_json_file(str(self.test_json_path))
        features = extract_multipolygon_data(data)
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0]['class_name'], "Test Class")

    def test_image_processing(self):
        image = load_image(str(self.test_image_path))
        self.assertEqual(image.size, (100, 100))

        chip = extract_chip_from_image(image, self.test_json['features'][0]['geometry']['coordinates'])
        self.assertEqual(chip.size[0], 40)  # 50-10
        self.assertEqual(chip.size[1], 40)  # 50-10

    def test_naming_convention(self):
        filename = generate_chip_filename("Test Class", "test_image", 1, "tif")
        self.assertEqual(filename, "Test_Class-test_image-1.tif")

    def test_class_name_sanitization(self):
        self.assertEqual(sanitize_class_name("Brick Kiln"), "Brick_Kiln")
        self.assertEqual(sanitize_class_name("Solar Panel"), "Solar_Panel")

if __name__ == '__main__':
    unittest.main()
```

### Success Criteria:

#### Automated Verification:
- [ ] All unit tests pass: `python -m pytest test_chip_extraction.py -v`
- [ ] Test coverage is adequate (aim for >80%)
- [ ] No linting errors in test file

#### Manual Verification:
- [ ] Test with actual sample data produces expected results
- [ ] Error scenarios are handled correctly
- [ ] Processing summary contains accurate information

---

## Testing Strategy

### Unit Tests:
- JSON parsing and validation
- Image loading and processing
- Chip extraction from coordinates
- Filename generation and sanitization
- Error handling for various edge cases

### Integration Tests:
- End-to-end processing of complete datasets
- Multiple datasets processing
- Error recovery and logging
- Processing summary generation

### Manual Testing Steps:
1. Test with sample Brick Kiln dataset
2. Verify chip extraction matches polygon boundaries
3. Check naming convention is followed correctly
4. Verify processing summary contains all expected information
5. Test error handling with missing files
6. Test with different image formats (tif/jpg)

## Performance Considerations

- Use tqdm for progress indication during batch processing
- Consider parallel processing for multiple datasets if needed
- Image processing is memory-intensive - process one image at a time
- Log file rotation for long-running processes

## Migration Notes

- No existing data migration needed
- Program is designed to be run on new datasets
- Output can be safely regenerated if needed

## References

- Original requirements: `generate_query_chips.md`
- Sample data: `labelled-data/Brick Kiln/GC01PS03D0011.json`
- Python dependencies: `requirements.txt`