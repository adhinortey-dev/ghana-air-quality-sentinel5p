"""Air quality assessment over Ghana using Sentinel-5P data.

This script uses Google Earth Engine and geemap to create an interactive map
showing NO2, CO, SO2, aerosol index, and a weighted-overlay air quality index.
"""

import ee
import geemap


AOI = ee.Geometry.Polygon(
    [
        [
            [-1.1659799208965849, 6.20294980302239],
            [-1.1659799208965849, 5.262862008051889],
            [0.8060659775409151, 5.262862008051889],
            [0.8060659775409151, 6.20294980302239],
        ]
    ]
)

START_DATE = "2023-01-01"
END_DATE = "2024-01-31"

POLLUTANT_WEIGHTS = {
    "NO2": 0.4,
    "CO": 0.2,
    "SO2": 0.2,
    "Aerosol": 0.2,
}


def initialize_earth_engine() -> None:
    """Initialize Earth Engine, prompting authentication when required."""
    try:
        ee.Initialize()
    except Exception:
        ee.Authenticate()
        ee.Initialize()


def get_classified_pollutant(
    pollutant: str,
    band: str,
    min_value: float,
    max_value: float,
    weight: float,
    palette: list[str],
    label: str,
) -> tuple[ee.Image, ee.Image, dict[str, object], str]:
    """Load, normalize, classify, and weight a Sentinel-5P pollutant layer."""
    dataset = (
        ee.ImageCollection(f"COPERNICUS/S5P/NRTI/L3_{pollutant}")
        .select(band)
        .filterDate(START_DATE, END_DATE)
        .mean()
        .clip(AOI)
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

    weighted = classified.multiply(weight)
    visualization = {"min": min_value, "max": max_value, "palette": palette}

    return dataset, weighted, visualization, label


def build_air_quality_map() -> geemap.Map:
    """Build the interactive geemap map with pollutant and AQI layers."""
    no2, no2_weighted, vis_no2, label_no2 = get_classified_pollutant(
        "NO2",
        "NO2_column_number_density",
        0,
        0.0002,
        POLLUTANT_WEIGHTS["NO2"],
        ["blue", "purple", "red", "yellow"],
        "NO2 Concentration",
    )

    co, co_weighted, vis_co, label_co = get_classified_pollutant(
        "CO",
        "CO_column_number_density",
        0,
        0.05,
        POLLUTANT_WEIGHTS["CO"],
        ["black", "brown", "orange", "yellow"],
        "CO Concentration",
    )

    so2, so2_weighted, vis_so2, label_so2 = get_classified_pollutant(
        "SO2",
        "SO2_column_number_density",
        0,
        0.0005,
        POLLUTANT_WEIGHTS["SO2"],
        ["blue", "cyan", "purple", "red"],
        "SO2 Concentration",
    )

    aerosol, aerosol_weighted, vis_aerosol, label_aerosol = get_classified_pollutant(
        "AER_AI",
        "absorbing_aerosol_index",
        -1,
        2,
        POLLUTANT_WEIGHTS["Aerosol"],
        ["green", "yellow", "orange", "red"],
        "Aerosol Index",
    )

    aqi_weighted_overlay = no2_weighted.add(co_weighted).add(so2_weighted).add(
        aerosol_weighted
    )
    aqi_normalized = aqi_weighted_overlay.divide(4)

    map_view = geemap.Map(center=[5.7, -0.2], zoom=7)
    map_view.addLayer(no2, vis_no2, label_no2)
    map_view.addLayer(co, vis_co, label_co)
    map_view.addLayer(so2, vis_so2, label_so2)
    map_view.addLayer(aerosol, vis_aerosol, label_aerosol)
    map_view.addLayer(
        aqi_normalized,
        {"min": 0, "max": 1, "palette": ["green", "yellow", "orange", "red"]},
        "Air Quality Index - Weighted Overlay",
    )
    map_view.addLayer(AOI, {"color": "white"}, "AOI Boundary")

    return map_view


def main() -> None:
    initialize_earth_engine()
    map_view = build_air_quality_map()
    map_view.to_html("ghana_air_quality_map.html")
    print("Saved interactive map to ghana_air_quality_map.html")


if __name__ == "__main__":
    main()
