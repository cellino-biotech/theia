# ===============================================================================
#    Use XY encoder output signals to drive camera acquisition during scan
# ===============================================================================

import json
import warnings
import numpy as np

from numpy import ndarray
from asi.asistage import MS2000
from basler.baslerace import ACA2040


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


def calc_col_filter(img_arr: ndarray) -> ndarray:
    col_filter_vals = np.empty((img_arr.shape[0], img_arr.shape[2]), dtype=np.float64)

    for i in range(img_arr.shape[0]):
        col_filter_vals[i] = np.average(img_arr[i], axis=0)

    return col_filter_vals


if __name__ == "__main__":
    # initialize devices
    cam = ACA2040(exposure_time_us=30)
    stage = MS2000("COM3", 115200)

    # query CRISP state
    if stage.get_crisp_state() != "F":
        # warnings.warn("CRISP not locked!")
        stage.lock_crisp()

    mid_point = (0, 0)  # scan mid-point
    scan_range_factor = 2  # number of overlapping fovs

    scan_range = scan_range_factor * cam.fov_height_mm
    total_row_acq = cam.sensor_height_pix * (scan_range_factor + 1)

    # configure camera triggers and IO
    cam.set_trigger()
    cam.set_io_control(line=2, source="ExposureActive")

    stage_vel = "{:.4f}".format(cam.sensor_pix_size_mm * cam.fps_max / 2)

    confirm = input(
        """This process will overwrite the current filter data. """
        """Make sure that the optical path is free of samples. """
        """Enter 'y' to continue... """
    )

    if confirm == "y":
        vals = {}

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

            col_filter_vals = calc_col_filter(img)

            # wait in case stage is still moving to start position
            stage.wait_for_device()

            vals[str(z)] = col_filter_vals.tolist()

        # save filtering values
        with open("./scripts/processing/cal_data_tilt.json", "w") as file:
            file.write(json.dumps(vals, indent=4))

    # housekeeping
    stage.close()
    cam.close()
