# ===============================================================================
#    Use XY encoder output signals to drive camera acquisition during scan
# ===============================================================================

import math
import json
import warnings
import numpy as np

from numpy import ndarray
from asi.asistage import MS2000
from basler.baslerace import ACA2040
from matplotlib import pyplot as plt


def row_shift(arr: ndarray, plot: bool = False) -> ndarray:
    arr = arr.astype(np.float64)
    rows = np.zeros((arr.shape[0],), dtype=int)

    for i in range(int(arr.shape[0] / 2)):
        # subtract corresponding image slices for reference
        subtraction = arr[i] - arr[-i - 1]

        err_baseline = np.sqrt(np.sum(np.square(subtraction)))

        # shift images by a fraction of original shape
        shift_y = math.trunc(arr.shape[1] / 10)

        err_y_down = np.empty((shift_y), dtype=np.float64)
        err_y_up = np.empty((shift_y), dtype=np.float64)

        err_y_down[0] = err_baseline
        err_y_up[0] = err_baseline

        # y-axis shift-down
        for r in range(1, shift_y):
            # subtract pixel values from first and last slices
            sub = arr[i][:-r] - arr[-i - 1][r:]
            err_y_down[r] = np.sqrt(np.sum(np.square(sub)))

        # y-axis shift-up
        for r in range(1, shift_y):
            # subtract pixel values from first and last slices
            sub = arr[i][r:] - arr[-i - 1][:-r]
            err_y_up[r] = np.sqrt(np.sum(np.square(sub)))

        vertex_down = np.amin(err_y_down)
        vertex_up = np.amin(err_y_up)

        if vertex_down < vertex_up:
            err_factor_y = np.where(err_y_down == vertex_down)[0][0]
            if err_factor_y > 0:
                rows[i] = -err_factor_y
                rows[-i - 1] = err_factor_y
            print(
                f"Remove {err_factor_y} rows from the bottom of plane {i} and "
                f"top of plane {len(arr) -i -1}"
            )
        else:
            err_factor_y = np.where(err_y_up == vertex_up)[0][0]
            if err_factor_y > 0:
                rows[i] = err_factor_y
                rows[-i - 1] = -err_factor_y
            print(
                f"Remove {err_factor_y} rows from the top of plane {i} and "
                f"bottom of plane {len(arr) -i -1}"
            )

    if plot:
        err_y = np.append(np.flip(err_y_down), err_y_up[1:])

        fig = plt.figure()
        ax = fig.add_axes([0, 0, 1, 1])
        ax.plot(np.linspace(-shift_y, shift_y - 1, num=shift_y * 2 - 1), err_y)
        fig.savefig("error_y.jpg", bbox_inches="tight")

    return rows


def col_shift(arr: ndarray, plot: bool = False) -> ndarray:
    arr = arr.astype(np.float64)
    cols = np.zeros((arr.shape[0],), dtype=int)

    for i in range(int(arr.shape[0] / 2)):
        # subtract corresponding image slices for reference
        subtraction = arr[i] - arr[-i - 1]

        err_baseline = np.sqrt(np.sum(np.square(subtraction)))

        shift_x = math.trunc(arr.shape[2] / 10)

        err_x_left = np.empty((shift_x), dtype=np.float64)
        err_x_right = np.empty((shift_x), dtype=np.float64)

        err_x_left[0] = err_baseline
        err_x_right[0] = err_baseline

        # x-axis shift-right
        for c in range(1, shift_x):
            # subtract pixel values from first and last slices
            sub = arr[i][:, c:] - arr[-i - 1][:, :-c]
            err_x_right[c] = np.sqrt(np.sum(np.square(sub)))

        # x-axis shift-left
        for c in range(1, shift_x):
            # subtract pixel values from first and last slices
            sub = arr[i][:, :-c] - arr[-i - 1][:, c:]
            err_x_left[c] = np.sqrt(np.sum(np.square(sub)))

        vertex_right = np.amin(err_x_right)
        vertex_left = np.amin(err_x_left)

        if vertex_right < vertex_left:
            err_factor_x = np.where(err_x_right == vertex_right)[0][0]
            if err_factor_x > 0:
                cols[i] = err_factor_x
                cols[-i - 1] = -err_factor_x
            print(
                f"Remove {err_factor_x} cols from the left of plane {i} and "
                f"right of plane {len(arr) -i -1}"
            )
        else:
            err_factor_x = np.where(err_x_left == vertex_left)[0][0]
            if err_factor_x > 0:
                cols[i] = -err_factor_x
                cols[-i - 1] = err_factor_x
            print(
                f"Remove {err_factor_x} cols from the right of plane {i} and "
                f"left of plane {len(arr) -i -1}"
            )

    if plot:
        err_x = np.append(np.flip(err_x_right), err_x_left[1:])

        fig = plt.figure()
        ax = fig.add_axes([0, 0, 1, 1])
        ax.plot(np.linspace(-shift_x, shift_x - 1, num=shift_x * 2 - 1), err_x)
        fig.savefig("error_x.jpg", bbox_inches="tight")

    return cols


def scan(
    stage: object,
    vel: float,
    mid_point: tuple,
    scan_range: float,
    fov_height: float,
    enc_divide: float,
    num_pix: int,
):
    # first move to mid-point y-value
    stage.set_speed(x=1, y=1)
    stage.move_axis("Y", mid_point[1])

    # wait for motors to reach position
    stage.wait_for_device()

    stage.set_speed(x=vel, y=vel)

    # invert TTL logic
    stage.ttl("F", -1)

    start = mid_point[0] - scan_range / 2 - fov_height / 2

    stage.scan_x_axis_enc(start=start, num_pix=num_pix, enc_divide=enc_divide)


if __name__ == "__main__":
    # initialize devices
    cam = ACA2040(exposure_time_us=30)
    stage = MS2000("COM3", 115200)

    # query CRISP state
    if stage.get_crisp_state() != "F":
        warnings.warn("CRISP not locked!")
        # stage.lock_crisp()

    mid_point = (0, 0)  # scan mid-point
    scan_range_factor = 2  # number of overlapping fovs

    scan_range = scan_range_factor * cam.fov_height_mm
    total_row_acq = cam.sensor_height_pix * (scan_range_factor + 1)

    # configure camera triggers and IO
    cam.set_trigger()
    cam.set_io_control(line=2, source="ExposureActive")

    stage_vel = "{:.4f}".format(cam.sensor_pix_size_mm * cam.fps_max / 2)

    confirm = input(
        """This process will overwrite the current alignment data. """
        """Make sure that the grid target is loaded and focused. """
        """Enter 'y' to continue... """
    )

    if confirm == "y":
        vals = {"2": {}, "3": {}, "4": {}, "5": {}, "6": {}, "7": {}}

        for z in range(2, 8):
            cam.set_roi_zones(z)

            # initiate scan and data acquisition
            scan(
                stage,
                stage_vel,
                mid_point,
                scan_range,
                cam.fov_height_mm,
                cam.sensor_pix_size_mm * 1e5,
                total_row_acq,
            )
            img = cam.acquire_stack(z, total_row_acq)

            vals[str(z)]["rows"] = row_shift(img).tolist()
            vals[str(z)]["cols"] = col_shift(img).tolist()

            # wait in case stage is still moving to start position
            stage.wait_for_device()

        # save filtering values
        with open("./scripts/processing/align_data_tilt.json", "w") as file:
            file.write(json.dumps(vals, indent=4))

    # housekeeping
    stage.close()
    cam.close()
