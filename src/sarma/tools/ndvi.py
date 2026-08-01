"""
Vegetation analysis tools.
"""


import numpy as np



def calculate_ndvi(
    image
):
    """
    Calculate NDVI from Sentinel-2.

    Formula:

        NDVI = (NIR - RED) / (NIR + RED)


    Requires:

        red
        nir08

    Returns:
        xarray DataArray
    """


    red = image.red

    nir = image.nir


    ndvi = (
        nir - red
    ) / (
        nir + red
    )


    return ndvi



def ndvi_statistics(
    ndvi
):
    """
    Calculate summary statistics.
    """


    stats = {

        "mean": float(
            ndvi.mean()
        ),

        "min": float(
            ndvi.min()
        ),

        "max": float(
            ndvi.max()
        )

    }


    return stats