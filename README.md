# Introduction

A vibe coded project to extract query chips from
large GeoTIFF files based on polygon coordinates
provided in GeoJSON format


## Format of json file

```json
{
  "type": "FeatureCollection",
  "name": "geotiff_file",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": 1,
        "Class Name": "Roof"
      },
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [
          [
            [
              [
                827,
                1530
              ],
              [
                827,
                1489
              ],
              [
                873,
                1489
              ],
              [
                873,
                1530
              ],
              [
                827,
                1530
              ]
            ]
          ]
        ]
      }
    }
  ]
}
```
## Vibe coding

Details on vibe coding prompt and progress are under [docs](./docs) folder.
Acknowledgements to numerous people who continues to help me with understanding
prompting.
