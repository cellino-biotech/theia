import math
import napari
import numpy as np
import tifffile as tf


class Correction:
    """Post-processing methods to correct image acquisitions"""

    def __init__(self, img: object):
        self.img = img

        if self.img.dtype not in (np.uint8, np.uint16):
            print(f"Image has unsuported data type {img.dtype}")
            raise TypeError
