#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from tqdm import tqdm
import time

from json_processor import load_json_file, extract_multipolygon_data, validate_json_structure
from image_processor import load_image, extract_chip_from_image, save_chip
from utils import generate_chip_filename, setup_logging, save_processing_summary, sanitize_class_name

logger = logging.getLogger(__name__)

def process_single_dataset(json_path: str, input_folder: str, output_folder: str,
                          extension: str = 'tif') -> Dict[str, Any]:
    """Process a single dataset (JSON + corresponding image)."""
    result = {
        'json_file': json_path,
        'status': 'success',
        'chips_created': 0,
        'polygons_found': 0,
        'polygons_processed': 0,
        'errors': [],
        'source_image': None
    }

    try:
        # Load and parse JSON
        json_data = load_json_file(json_path)
        filename = json_data.get('name', Path(json_path).stem)

        # Find corresponding image file in the same directory as the JSON file
        json_dir = Path(json_path).parent
        source_image_path = json_dir / f"{filename}.{extension}"

        # Check if the specified image exists and is valid
        if not source_image_path.exists():
            result['status'] = 'error'
            result['errors'].append(f"Source image not found: {source_image_path}")
            return result

        try:
            test_image_data = load_image(str(source_image_path))
            logger.debug(f"Successfully loaded image: {source_image_path}")
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(f"Could not load source image {source_image_path}: {e}")
            return result

        if not source_image_path:
            result['status'] = 'error'
            result['errors'].append(f"Source image not found for {filename}")
            return result

        result['source_image'] = source_image_path

        # Load source image
        image_data = load_image(str(source_image_path))

        # Extract MultiPolygon data
        multipolygon_data = extract_multipolygon_data(json_data)
        result['polygons_found'] = len(multipolygon_data)

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
                chip = extract_chip_from_image(image_data, coordinates)

                # Generate filename
                chip_filename = generate_chip_filename(class_name, filename, i + 1, extension)
                chip_path = Path(output_folder) / chip_filename

                # Save chip
                save_chip(chip, str(chip_path))
                result['chips_created'] += 1
                result['polygons_processed'] += 1

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
                        help='Source image extension to process (default: tif). Only files with this extension will be processed.')
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
    print(f"Total polygons found: {summary['total_polygons_found']}")
    print(f"Total polygons processed: {summary['total_polygons_processed']}")
    print(f"Processing time: {summary['processing_time']:.2f} seconds")
    print(f"Summary saved to: {args.output_folder}/processing_summary.json")
    print("="*50)

def generate_processing_summary(results: List[Dict], total_files: int, start_time: float) -> Dict[str, Any]:
    """Generate processing summary statistics."""
    successful_count = sum(1 for r in results if r['status'] == 'success')
    partial_success_count = sum(1 for r in results if r['status'] == 'partial_success')
    failed_count = sum(1 for r in results if r['status'] == 'error')
    total_chips = sum(r['chips_created'] for r in results)
    total_polygons_found = sum(r['polygons_found'] for r in results)
    total_polygons_processed = sum(r['polygons_processed'] for r in results)

    return {
        'total_files_processed': total_files,
        'successful_count': successful_count,
        'partial_success_count': partial_success_count,
        'failed_count': failed_count,
        'total_chips_created': total_chips,
        'total_polygons_found': total_polygons_found,
        'total_polygons_processed': total_polygons_processed,
        'processing_time': time.time() - start_time,
        'results': results
    }

if __name__ == '__main__':
    main()