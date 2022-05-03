# ===============================================================================
#    Use XY encoder output signals to drive camera acquisition during scan
# ===============================================================================

import json
import warnings
import numpy as np

from numpy import ndarray
from asi.asistage import MS2000
from basler.baslerace import ACA2040


# explicit constants
SENSOR_WIDTH_PIX = 2064
SENSOR_HEIGHT_PIX = 1544
PIX_SIZE_MM = 0.35e-3  # determined from ImageJ
EXPOSURE_TIME_US = 30  # given max light intensity
FPS_MAX = 635

# inferred constants
FOV_HEIGHT_MM = SENSOR_HEIGHT_PIX * PIX_SIZE_MM
SCAN_VEL_MM_S = PIX_SIZE_MM * FPS_MAX / 2
ENC_DIVIDE = PIX_SIZE_MM * 10e4


def scan(stage: object, mid_point: tuple, scan_range: float, num_pix: int):
    # first move to mid-point y-value
    stage.set_speed(x=1, y=1)
    stage.move_axis("Y", mid_point[1])

    # wait for motors to stop to prevent backlash interference
    stage.wait_for_device()

    stage.set_speed(x=SCAN_VEL_MM_S, y=SCAN_VEL_MM_S)

    # invert TTL logic
    stage.ttl("F", -1)

    start = mid_point[0] - scan_range / 2 - FOV_HEIGHT_MM / 2

    stage.scan_x_axis_enc(start=start, num_pix=num_pix, enc_divide=ENC_DIVIDE)


def calc_col_filter(img_arr: ndarray) -> ndarray:
    col_filter_vals = np.empty((img_arr.shape[0], img_arr.shape[2]), dtype=np.float64)

    for i in range(img_arr.shape[0]):
        col_filter_vals[i] = np.mean(img_arr[i], axis=0)

    return col_filter_vals


if __name__ == "__main__":
    mid_point = (0, 0)  # scan mid-point
    scan_range_factor = 2  # number of overlapping fovs
    scan_range = scan_range_factor * FOV_HEIGHT_MM
    total_row_acq = SENSOR_HEIGHT_PIX * (scan_range_factor + 1)

    # connect to stage serial port
    stage = MS2000("COM3", 115200)

    # query CRISP state
    if stage.get_crisp_state() != "F":
        warnings.warn("CRISP not locked!")

    # configure camera object
    camera = ACA2040(exp_time=EXPOSURE_TIME_US)
    camera.set_trigger()
    camera.set_io_control(line=2, source="ExposureActive")

    confirm = input(
        """This process will overwrite the current filter data. """
        """Make sure that the optical path is free of samples. """
        """Enter 'y' to continue... """
    )

    if confirm == "y":
        vals = {}

        for z in range(2, 8):
            camera.set_roi_zones(z)

            # initiate scan and data acquisition
            scan(stage, mid_point, scan_range, total_row_acq)
            img = camera.acquire(z, total_row_acq)

            col_filter_vals = calc_col_filter(img)

            # wait in case stage is still moving to start position
            stage.wait_for_device()

            vals[str(z)] = col_filter_vals.tolist()

        # save filtering values
        with open("./scripts/processing/filter_vals.json", "w") as file:
            file.write(json.dumps(vals, indent=4))

    # housekeeping
    stage.close()
    camera.close()
