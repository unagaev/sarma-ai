from sarma.tools.worldcover import (
    load_aoi,
    download_tiles,
    clip_to_aoi,
    landcover_statistics
)

from sarma.tools.sentinel import (
    search_sentinel2,
    load_sentinel2,
    create_mosaic
)

from sarma.tools.ndvi import calculate_ndvi


def analyse_area():

    # ---------------------
    # AOI
    # ---------------------

    aoi = load_aoi()


    # ---------------------
    # LAND COVER
    # ---------------------

    tiles = download_tiles(aoi)

    worldcover_image, meta = clip_to_aoi(
        tiles,
        aoi
    )

    landcover = landcover_statistics(
        worldcover_image
    )


    # ---------------------
    # SENTINEL-2
    # ---------------------

    items = search_sentinel2(
        aoi,
        "2026-06-01/2026-08-01"
    )


    sentinel_data = load_sentinel2(
        items,
        aoi,
        bands=[
            "red",
            "nir"
        ]
    )


    sentinel_image = create_mosaic(
        sentinel_data
    )


    # ---------------------
    # NDVI
    # ---------------------

    ndvi_value = calculate_ndvi(
        sentinel_image
    )


    return {

        "land_cover": landcover,

        "ndvi_mean": float(
            ndvi_value.mean()
        ),

        "description":
        "Satellite environmental analysis"

    }
