# ===============================================================================
#    Use XY encoder output signals to drive camera acquisition during scan
# ===============================================================================

import os
import json

from datetime import datetime
from ni.daq import DAQ
from asi.asistage import MS2000
from basler.baslerace import ACA2040
from processing.corrections import Correction


# explicit constants
SENSOR_WIDTH_PIX = 2064
SENSOR_HEIGHT_PIX = 1544
PIX_SIZE_MM = 0.35e-3  # determined from ImageJ
EXPOSURE_TIME_US = 50  # given max light intensity
FPS_MAX = 635

# inferred constants
FOV_HEIGHT_MM = SENSOR_HEIGHT_PIX * PIX_SIZE_MM
SCAN_VEL_MM_S = PIX_SIZE_MM * FPS_MAX
ENC_DIVIDE = PIX_SIZE_MM * 10e4


def create_data_dir():
    now = datetime.now()
    dirname = now.strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join("C:\\Users\\lukas\\Data", dirname)
    os.mkdir(path)
    return (path, dirname)


def scan(stage: object, mid_point: tuple, scan_range: float, num_pix: int):
    # first move to mid-point y-value
    stage.set_speed(x=1, y=1)
    stage.move_axis("Y", mid_point[1])
    stage.wait_for_device()

    stage.set_speed(x=SCAN_VEL_MM_S, y=SCAN_VEL_MM_S)

    # invert TTL logic
    stage.ttl("F", -1)

    start = mid_point[0] - scan_range / 2 - FOV_HEIGHT_MM / 2

    stage.scan_x_axis_enc(start=start, num_pix=num_pix, enc_divide=ENC_DIVIDE)

    stage.close()


if __name__ == "__main__":
    path, dirname = create_data_dir()

    mid_point = (0, 0)  # scan mid-point
    num_zones = 5  # number of image slices
    scan_range_factor = 1  # number of overlapping fovs
    scan_range = scan_range_factor * FOV_HEIGHT_MM
    total_row_acq = SENSOR_HEIGHT_PIX * (scan_range_factor + 1)

    # connect to stage serial port
    stage = MS2000("COM3", 115200)

    # check CRISP state
    crisp_state = stage.get_crisp_state()
    if crisp_state != "F":
        print("CRISP not locked!")

    # configure camera object
    camera = ACA2040(exp_time=EXPOSURE_TIME_US)
    camera.set_trigger()
    camera.digital_io_control(line=2, source="ExposureActive")
    camera.set_roi_zones(num_zones)

    # daq = DAQ(total_row_acq)

    # initiate scan and data acquisition
    scan(stage, mid_point=mid_point, scan_range=scan_range, num_pix=total_row_acq)
    # daq.start()
    camera.acquire(path, dirname, num_zones, total_row_acq)
    # daq.plot_data()
    # daq.stop()

    correction = Correction(os.path.join(path, dirname + "_overlap.tif"))
    with open("filter_vals.json") as file:
        col_filter_vals = json.loads(file.read())

    col_filter_vals = col_filter_vals["data"]
    correction.apply_col_filter(col_filter_vals)
    correction.full_correction()
    correction.save(os.path.join(path, dirname + "_proc.tif"))
    correction.show()

    # col_filter_vals = correction.calculate_col_filter()

    # with open("filter_vals.json", "w") as file:
    #     file.write(json.dumps({"data": col_filter_vals.tolist()}))

    params = {
        "total_reconstructions": num_zones,
        "total_overlap_fovs": scan_range_factor,
        "scan_midpoint": mid_point,
        "scan_range": scan_range,
    }

    fname = os.path.join(path, dirname + "_params.json")

    with open(fname, "w") as file:
        file.write(json.dumps(params))
