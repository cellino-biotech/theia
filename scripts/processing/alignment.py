import os
import json
import numpy as np

from numpy import ndarray


def reformat(arr: ndarray) -> ndarray:
    if arr.dtype != np.float64:
        if arr.dtype in (np.uint8, np.uint16):
            return arr.astype(np.float64)
        else:
            print(f"Image has unsuported data type {arr.dtype}")
            raise TypeError
    else:
        return arr


def crop(arr: list) -> ndarray:
    shape = list(arr[0].shape)

    for i in arr:
        if i.shape[0] < shape[0]:
            shape[0] = i.shape[0]
        if i.shape[1] < shape[1]:
            shape[1] = i.shape[1]

    for i in range(len(arr)):
        if arr[i].shape[0] > shape[0]:
            diff = arr[i].shape[0] - shape[0]

            if diff % 2:
                arr[i] = arr[i][int(diff / 2) + 1 : int(-diff / 2)]
            else:
                arr[i] = arr[i][int(diff / 2) : int(-diff / 2)]

        if arr[i].shape[1] > shape[1]:
            diff = arr[i].shape[1] - shape[1]

            if diff % 2:
                arr[i] = arr[i][:, int(diff / 2) + 1 : int(-diff / 2)]
            else:
                arr[i] = arr[i][:, int(diff / 2) : int(-diff / 2)]

    return np.stack(arr, axis=0).astype(np.uint16)


def align(arr: ndarray) -> ndarray:
    arr = reformat(arr)

    # for easier processing, break image stack into list
    arr = [arr[i] for i in range(arr.shape[0])]

    # read alignment data file
    file_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "align_data_tilt.json"
    )
    if os.path.exists(file_dir):
        with open(file_dir) as file:
            align_data = json.loads(file.read())

        # extract data corresponding to the number of image planes
        align_data = align_data[str(len(arr))]

        for i in range(len(arr)):
            row_shift = align_data["rows"][i]
            if row_shift < 0:
                # shift down
                arr[i] = arr[i][:row_shift]
            elif row_shift > 0:
                # shift up
                arr[i] = arr[i][row_shift:]
            else:
                pass

            col_shift = align_data["cols"][i]
            if col_shift < 0:
                # shift right
                arr[i] = arr[i][:, :col_shift]
            elif col_shift > 0:
                # shift left
                arr[i] = arr[i][:, col_shift:]
            else:
                pass

    return crop(arr)
