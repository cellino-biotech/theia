import os
import json
import warnings
import numpy as np

from numpy import ndarray


def apply_col_filter(img_arr: ndarray):
    """Remove artifact interference patterns from imaging planes

    Assume filter values file is located in same parent directory
    """
    file_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "cal_data_tilt.json"
    )
    if os.path.exists(file_dir):
        with open(file_dir) as file:
            cal_data = json.loads(file.read())

        # extract data corresponding to the number of image planes
        cal_data = cal_data[str(img_arr.shape[0])]

        # use either amin or mean
        cal_data = np.multiply(cal_data, (1 / np.mean(cal_data)))

        for p in range(img_arr.shape[0]):
            for r in range(img_arr.shape[1]):
                img_arr[p][r] = img_arr[p][r] / cal_data[p]

        return img_arr
    else:
        warnings.warn("Missing filter values file!")
