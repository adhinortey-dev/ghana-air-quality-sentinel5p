# Air Quality Assessment in Ghana Using Sentinel-5P

This project uses Google Earth Engine satellite data to assess air quality over a selected area of Ghana. It processes Sentinel-5P pollutant layers and combines them with a weighted overlay method to produce a composite air quality index.

## Project Overview

The workflow analyzes four atmospheric indicators:

- Nitrogen dioxide (`NO2`)
- Carbon monoxide (`CO`)
- Sulfur dioxide (`SO2`)
- Aerosol index as a proxy indicator for fine particulate pollution

Each pollutant layer is filtered by date, clipped to the study area, normalized, classified, weighted, and combined into a final air quality index layer.

## Study Period

January 1, 2023 to January 31, 2024

## Tools Used

- Python
- Google Earth Engine
- Folium
- Sentinel-5P
- Weighted overlay analysis

## Repository Structure

```text
.
|-- src/
|   `-- air_quality_assessment.py
|-- .gitignore
|-- LICENSE
|-- README.md
`-- requirements.txt
```

## How To Run

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the script:

```bash
python src/air_quality_assessment.py
```

The first run may ask you to authenticate with Google Earth Engine. After a successful run, the script saves an interactive map as:

```text
ghana_air_quality_map.html
```

## Methodology

1. Define the Ghana area of interest with a polygon.
2. Load Sentinel-5P pollutant image collections from Google Earth Engine.
3. Filter each collection by date and calculate the mean pollutant surface.
4. Normalize each pollutant layer to a 0-1 scale.
5. Reclassify normalized values into four pollution categories.
6. Apply pollutant weights:
   - `NO2`: 0.4
   - `CO`: 0.2
   - `SO2`: 0.2
   - Aerosol index: 0.2
7. Combine weighted layers into a composite air quality index.
8. Visualize individual pollutant layers and the final index on an interactive map.

## Notes

This public version contains the cleaned source code and project explanation. Original academic submission documents were not included because they contain personal student information.
