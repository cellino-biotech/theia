# ===============================================================================
#    Use XY encoder output signals to drive camera acquisition during scan
# ===============================================================================

import os
import json
import warnings

from datetime import datetime
from ni.daq import DAQ
from asi.asistage import MS2000
from basler.baslerace import ACA2040
from processing.corrections import Correction


def create_data_dir():
    now = datetime.now()
    dirname = now.strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join("C:\\Users\\lukas\\Data", dirname)
    os.mkdir(path)
    return (path, dirname)


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
    start = "{:.6f}".format(start)

    stage.scan_x_axis_enc(start=start, num_pix=num_pix, enc_divide=enc_divide)


if __name__ == "__main__":
    path, dirname = create_data_dir()

    # initialize devices
    cam = ACA2040(exposure_time_us=30)
    stage = MS2000("COM3", 115200)

    # query CRISP state
    if stage.get_crisp_state() != "F":
        warnings.warn("CRISP may not be locked!")
        # stage.lock_crisp()

    mid_point = (0, 0)  # scan mid-point
    num_zones = 5  # number of image slices
    scan_range_factor = 20  # number of overlapping fovs

    scan_range = scan_range_factor * cam.fov_height_mm
    total_row_acq = cam.sensor_height_pix * (scan_range_factor + 1)

    # restrict stage velocity to 4 decimal places
    stage_vel = "{:.4f}".format(cam.sensor_pix_size_mm * cam.fps_max / 2)

    # configure camera triggers, zones, and IO
    cam.set_trigger()
    cam.set_io_control(line=2, source="ExposureActive")
    cam.set_roi_zones(num_zones)

    # initialize DAQ
    # daq = DAQ(total_row_acq)

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
    # daq.start()
    img = cam.acquire_stack(num_zones, total_row_acq)
    # daq.plot_data()
    # daq.stop()

    img = cam.crop_overlap_zone(img)

    correction = Correction(img)
    correction.apply_col_filter()
    correction.apply_full_correction()

    img_raw = cam.format_image_array(img)
    img_proc = cam.format_image_array(correction.crop_arr)

    # save imaging data
    cam.save_image_array(img_raw, os.path.join(path, dirname + "_raw.tif"))
    cam.save_image_array(img_proc, os.path.join(path, dirname + "_proc.tif"))

    params = {
        "total_reconstructions": num_zones,
        "total_overlap_fovs": scan_range_factor,
        "scan_midpoint": mid_point,
        "scan_range": scan_range,
        "scan_velocity_mm_s": stage_vel,
        "exposure_time_us": cam.exposure_time_us,
        "pixel_size_mm": cam.sensor_pix_size_mm,
    }

    fname = os.path.join(path, dirname + "_params.json")
    with open(fname, "w") as file:
        file.write(json.dumps(params, indent=4))

    # housekeeping
    stage.close()
    cam.close()

    correction.show()
