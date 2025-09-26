import unittest
import tempfile
import json
from pathlib import Path
from PIL import Image
import numpy as np

from json_processor import load_json_file, extract_multipolygon_data
from image_processor import load_image, extract_chip_from_image
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