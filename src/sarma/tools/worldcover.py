from pathlib import Path

import requests
import numpy as np

import geopandas as gpd

import rasterio
from rasterio.merge import merge
from rasterio.mask import mask

from tqdm.auto import tqdm


# =====================================================
# PATHS
# =====================================================

BASE_DIR = Path(
    r"C:\Users\rost8\OneDrive\Desktop\SARMA\src\sarma\tools"
)

AOI_FILE = BASE_DIR / "aoi" / "NT-Polygon-2026.geojson"

DOWNLOAD_DIR = BASE_DIR / "downloads" 
DOWNLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = BASE_DIR / "worldcover_clip.tif"


# =====================================================
# WORLD COVER SETTINGS
# =====================================================

S3_PREFIX = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com"
)

GRID_URL = (
    f"{S3_PREFIX}/esa_worldcover_grid.geojson"
)

YEAR = 2021
VERSION = "v200"


CLASS_NAMES = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen",
}


# =====================================================
# AOI
# =====================================================

def load_aoi():

    gdf = gpd.read_file(
        AOI_FILE
    )

    if gdf.empty:
        raise ValueError(
            "AOI is empty"
        )

    gdf = gdf.to_crs(
        "EPSG:4326"
    )

    return gdf.unary_union



# =====================================================
# DOWNLOAD TILES
# =====================================================

def download_tiles(aoi):

    print("Loading WorldCover grid...")

    grid = gpd.read_file(
        GRID_URL
    )

    tiles = grid[
        grid.intersects(aoi)
    ]


    print(
        f"Required tiles: {len(tiles)}"
    )


    downloaded = []


    for tile in tqdm(
        tiles.ll_tile
    ):

        filename = (
            f"ESA_WorldCover_10m_"
            f"{YEAR}_{VERSION}_{tile}_Map.tif"
        )


        url = (
            f"{S3_PREFIX}/"
            f"{VERSION}/{YEAR}/map/"
            f"{filename}"
        )


        outfile = (
            DOWNLOAD_DIR /
            filename
        )


        if not outfile.exists():

            print(
                "Downloading:",
                filename
            )

            response = requests.get(
                url
            )

            response.raise_for_status()


            with open(
                outfile,
                "wb"
            ) as f:

                f.write(
                    response.content
                )


        downloaded.append(
            outfile
        )


    return downloaded



# =====================================================
# MERGE + CLIP
# =====================================================

def clip_to_aoi(
        tile_files,
        aoi
):

    datasets = [
        rasterio.open(
            f
        )
        for f in tile_files
    ]


    mosaic, transform = merge(
        datasets
    )


    meta = datasets[0].meta.copy()


    meta.update(
        {
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": transform
        }
    )


    with rasterio.io.MemoryFile() as mem:

        with mem.open(
            **meta
        ) as src:

            src.write(
                mosaic
            )


            clipped, clipped_transform = mask(
                src,
                [aoi],
                crop=True
            )


    meta.update(
        {
            "height": clipped.shape[1],
            "width": clipped.shape[2],
            "transform": clipped_transform
        }
    )


    return clipped, meta



# =====================================================
# STATISTICS
# =====================================================

def landcover_statistics(
        image
):

    arr = image[0]


    values, counts = np.unique(
        arr,
        return_counts=True
    )


    total = counts.sum()


    stats = {}


    for value, count in zip(
        values,
        counts
    ):

        stats[
            CLASS_NAMES.get(
                value,
                str(value)
            )
        ] = float(
            round(
            count / total * 100,
            2
          )
        )


    return stats



# =====================================================
# SAVE
# =====================================================

def save_raster(
        image,
        meta
):

    with rasterio.open(
        OUTPUT_FILE,
        "w",
        **meta
    ) as dst:

        dst.write(
            image
        )



# =====================================================
# MAIN
# =====================================================

def main():

    print(
        "Loading AOI..."
    )

    aoi = load_aoi()


    tiles = download_tiles(
        aoi
    )


    print(
        "Clipping WorldCover..."
    )

    image, meta = clip_to_aoi(
        tiles,
        aoi
    )


    print(
        "Saving raster..."
    )

    save_raster(
        image,
        meta
    )


    print(
        "\nLand cover statistics:"
    )

    stats = landcover_statistics(
        image
    )

    
    for k, v in stats.items():

        print(
            f"{k}: {v}%"
        )


    print(
        "\nSaved:",
        OUTPUT_FILE
    )



if __name__ == "__main__":
    main()