## Generate Query Chips


### Input
The labelled-data folder contains labelled data-set. 
Every sub-folder inside the `labelled-data` folder contains tif, jpg and a json file.
The json file contains multipolygon details providing the pixel coordinates (bounding boxes) of the features within the named file.

### Goal

- Read the json file
- Read the `name` parameter in the json file which points to the source image - {name}.{ext}. {ext} can be jpg or tif
- Extract chip from the {name}.{ext} based on the pixel coordinates in the json file
- Name the chip file as {class-name}-{filename}-{idx}.{ext}
  example `STP-GC01PS03D0076-1.tif`, `STP-GC01PS03D0076-2.tif` `STP-GC01PS03D0076-1.jpg` etc


#### Implementation note

- Take as input the folder containing all labelled data set
- Take as input the source file extension to process. Default being `tif`
- Use output folder option, default being `output`
- Use python
- Use modular and reusable functions to read json, read "MultiPolygon" coordinates, read tif, read jpg, extracting polygon from jpg and tif
- Fail early and explicitly. No silent fallback.
- Use "source .venv/bin/activate" to activate the venv
- Use "uv pip install <package>" in the venv
- Use `rasterio` to process `tif` files which are GeoTIFFs. Use `PIL` to process `jpg`
- Save progress in progress.md
- Save the plan as plan.md and progress as progress.md
