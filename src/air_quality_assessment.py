"""Air quality assessment over Ghana using Sentinel-5P data.

This script uses Google Earth Engine and Folium to create an interactive map
showing NO2, CO, SO2, aerosol index, and a weighted-overlay air quality index.
"""

import ee
import folium
import os


START_DATE = "2023-01-01"
END_DATE = "2024-01-31"

POLLUTANT_WEIGHTS = {
    "NO2": 0.4,
    "CO": 0.2,
    "SO2": 0.2,
    "Aerosol": 0.2,
}


def get_area_of_interest() -> ee.Geometry:
    """Return the Ghana area of interest used for this analysis."""
    return ee.Geometry.Polygon(
        [
            [
                [-1.1659799208965849, 6.20294980302239],
                [-1.1659799208965849, 5.262862008051889],
                [0.8060659775409151, 5.262862008051889],
                [0.8060659775409151, 6.20294980302239],
            ]
        ]
    )


def initialize_earth_engine() -> None:
    """Initialize Earth Engine, prompting authentication when required."""
    project = os.environ.get("EE_PROJECT")
    try:
        ee.Initialize(project=project)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=project)


def get_classified_pollutant(
    pollutant: str,
    band: str,
    min_value: float,
    max_value: float,
    weight: float,
    palette: list[str],
    label: str,
    area_of_interest: ee.Geometry,
) -> tuple[ee.Image, ee.Image, dict[str, object], str]:
    """Load, normalize, classify, and weight a Sentinel-5P pollutant layer."""
    aoi_mask = ee.Image.constant(1).clip(area_of_interest).selfMask()
    dataset = (
        ee.ImageCollection(f"COPERNICUS/S5P/NRTI/L3_{pollutant}")
        .select(band)
        .filterDate(START_DATE, END_DATE)
        .mean()
        .clip(area_of_interest)
        .updateMask(aoi_mask)
    )

    normalized = dataset.subtract(min_value).divide(max_value - min_value).clamp(0, 1)
    classified = normalized.expression(
        "(b1 <= T1) ? C1"
        " : (b1 <= T2) ? C2"
        " : (b1 <= T3) ? C3"
        " : C4",
        {
            "b1": normalized,
            "T1": 0.25,
            "C1": 1,
            "T2": 0.50,
            "C2": 2,
            "T3": 0.75,
            "C3": 3,
            "C4": 4,
        },
    )

    weighted = classified.multiply(weight).updateMask(aoi_mask)
    visualization = {"min": min_value, "max": max_value, "palette": palette}

    return dataset, weighted, visualization, label


def add_ee_layer(
    map_view: folium.Map,
    ee_object: ee.Image | ee.Geometry,
    visualization: dict[str, object],
    name: str,
) -> None:
    """Add an Earth Engine image or geometry layer to a Folium map."""
    if isinstance(ee_object, ee.Geometry):
        ee_object = ee.Image().paint(ee_object, 0, 2)

    map_id = ee.Image(ee_object).getMapId(visualization)
    folium.raster_layers.TileLayer(
        tiles=map_id["tile_fetcher"].url_format,
        attr="Google Earth Engine",
        name=name,
        overlay=True,
        control=True,
    ).add_to(map_view)


def add_aoi_outline(map_view: folium.Map) -> None:
    """Add the study area as a transparent polygon outline."""
    coordinates = [
        [6.20294980302239, -1.1659799208965849],
        [5.262862008051889, -1.1659799208965849],
        [5.262862008051889, 0.8060659775409151],
        [6.20294980302239, 0.8060659775409151],
        [6.20294980302239, -1.1659799208965849],
    ]
    folium.Polygon(
        locations=coordinates,
        color="black",
        weight=2,
        fill=False,
        tooltip="Area of Interest",
        name="AOI Boundary",
    ).add_to(map_view)


def build_air_quality_map() -> folium.Map:
    """Build the interactive Folium map with pollutant and AQI layers."""
    area_of_interest = get_area_of_interest()

    no2, no2_weighted, vis_no2, label_no2 = get_classified_pollutant(
        "NO2",
        "NO2_column_number_density",
        0,
        0.0002,
        POLLUTANT_WEIGHTS["NO2"],
        ["blue", "purple", "red", "yellow"],
        "NO2 Concentration",
        area_of_interest,
    )

    co, co_weighted, vis_co, label_co = get_classified_pollutant(
        "CO",
        "CO_column_number_density",
        0,
        0.05,
        POLLUTANT_WEIGHTS["CO"],
        ["black", "brown", "orange", "yellow"],
        "CO Concentration",
        area_of_interest,
    )

    so2, so2_weighted, vis_so2, label_so2 = get_classified_pollutant(
        "SO2",
        "SO2_column_number_density",
        0,
        0.0005,
        POLLUTANT_WEIGHTS["SO2"],
        ["blue", "cyan", "purple", "red"],
        "SO2 Concentration",
        area_of_interest,
    )

    aerosol, aerosol_weighted, vis_aerosol, label_aerosol = get_classified_pollutant(
        "AER_AI",
        "absorbing_aerosol_index",
        -1,
        2,
        POLLUTANT_WEIGHTS["Aerosol"],
        ["green", "yellow", "orange", "red"],
        "Aerosol Index",
        area_of_interest,
    )

    aqi_weighted_overlay = no2_weighted.add(co_weighted).add(so2_weighted).add(
        aerosol_weighted
    )
    aoi_mask = ee.Image.constant(1).clip(area_of_interest).selfMask()
    aqi_normalized = aqi_weighted_overlay.divide(4).updateMask(aoi_mask)

    map_view = folium.Map(location=[5.7, -0.2], zoom_start=7, tiles="OpenStreetMap")
    add_ee_layer(map_view, no2, vis_no2, label_no2)
    add_ee_layer(map_view, co, vis_co, label_co)
    add_ee_layer(map_view, so2, vis_so2, label_so2)
    add_ee_layer(map_view, aerosol, vis_aerosol, label_aerosol)
    add_ee_layer(
        map_view,
        aqi_normalized,
        {"min": 0, "max": 1, "palette": ["green", "yellow", "orange", "red"]},
        "Air Quality Index - Weighted Overlay",
    )
    add_aoi_outline(map_view)
    folium.LayerControl(collapsed=False).add_to(map_view)

    return map_view


def main() -> None:
    initialize_earth_engine()
    map_view = build_air_quality_map()
    map_view.save("ghana_air_quality_map.html")
    print("Saved interactive map to ghana_air_quality_map.html")


if __name__ == "__main__":
    main()
