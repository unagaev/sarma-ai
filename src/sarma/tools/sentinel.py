"""
Sentinel-2 geospatial tools for SARMA.

Responsibilities:
- Load AOI
- Query Sentinel-2 STAC catalog
- Load Sentinel-2 bands
- Create temporal composite
"""


from pathlib import Path

import geopandas as gpd

from shapely.geometry import mapping

from pystac_client import Client

import odc.stac
import odc.geo.xr


# =====================================================
# STAC CONFIGURATION
# =====================================================

STAC_URL = (
    "https://earth-search.aws.element84.com/v1"
)

catalog = Client.open(STAC_URL)


# =====================================================
# SENTINEL BANDS
# =====================================================

DEFAULT_BANDS = [
    "coastal",
    "blue",
    "green",
    "red",
    "rededge1",
    "rededge2",
    "rededge3",
    "nir",
    "nir08",
    "nir09",
    "swir16",
    "swir22",
]


# =====================================================
# AOI
# =====================================================

def load_aoi(
    filepath: str
):
    """
    Load AOI polygon.

    Returns:
        shapely geometry
    """

    gdf = gpd.read_file(filepath)


    if gdf.empty:
        raise ValueError(
            "AOI contains no geometry"
        )


    # STAC requires WGS84
    gdf = gdf.to_crs(
        "EPSG:4326"
    )


    # merge multiple polygons
    geom = gdf.unary_union


    return geom



# =====================================================
# SEARCH SENTINEL-2
# =====================================================

def search_sentinel2(
    geom,
    date_range,
    cloud_limit=25
):
    """
    Search Sentinel-2 Level-2A imagery.

    Parameters
    ----------
    geom:
        shapely geometry

    date_range:
        Example:
        "2026-07-01/2026-07-31"

    cloud_limit:
        Maximum cloud percentage

    Returns
    -------
    list
        STAC items
    """


    search = catalog.search(
        collections=[
            "sentinel-2-l2a"
        ],

        intersects=mapping(
            geom
        ),

        datetime=date_range,

        query={
            "eo:cloud_cover": {
                "lt": cloud_limit
            }
        }
    )


    items = list(
        search.items()
    )


    print(
        f"Found {len(items)} Sentinel-2 scenes"
    )


    return items



# =====================================================
# LOAD IMAGERY
# =====================================================

def load_sentinel2(
    items,
    geom,
    bands=None,
    resolution=10
):
    """
    Load Sentinel-2 data using odc-stac.
    """


    if bands is None:
        bands = DEFAULT_BANDS


    data = odc.stac.load(
        items,

        bands=bands,

        geopolygon=geom,

        resolution=resolution,

        groupby="time",

        chunks={}
    )


    return data



# =====================================================
# CREATE MOSAIC
# =====================================================

def create_mosaic(
    data,
    bands=None
):
    """
    Create simple temporal composite.

    Missing pixels are filled
    from neighbouring dates.
    """


    if "time" not in data.dims:
        raise ValueError(
            "Dataset has no time dimension"
        )


    mosaic = (
        data
        .where(data != 0)
        .bfill(
            dim="time"
        )
        .isel(
            time=0
        )
    )


    if bands:
        mosaic = mosaic[bands]


    return mosaic



# =====================================================
# SAVE COG
# =====================================================

def save_cog(
    image,
    filename
):
    """
    Save Cloud Optimized GeoTIFF.
    """

    odc.geo.xr.write_cog(
        image,
        fname=filename,
        overwrite=True
    )