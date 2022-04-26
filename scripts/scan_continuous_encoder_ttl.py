# ===============================================================================
#    Use XY encoder output signals to drive camera acquisition during scan
# ===============================================================================

import os
import json
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime
from asi.asistage import MS2000
from basler.baslerace import ACA2040

import nidaqmx
from nidaqmx.stream_readers import CounterReader
from nidaqmx.constants import AcquisitionType, CountDirection, Edge


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

    start = mid_point[0] - scan_range / 2 - FOV_HEIGHT_MM / 2

    stage.scan_x_axis_enc(start=start, num_pix=num_pix, enc_divide=ENC_DIVIDE)

    stage.close()


def daq_config(total_row_acq: int) -> tuple:
    total_ticks = total_row_acq

    ci_task = nidaqmx.Task()

    channel = ci_task.ci_channels.add_ci_count_edges_chan(
        "Dev1/ctr0",
        initial_count=0,
        edge=Edge.FALLING,
        count_direction=CountDirection.COUNT_UP,
    )

    channel.ci_count_edges_term = "PFI0"

    ci_task.timing.cfg_samp_clk_timing(
        rate=50000,
        source="PFI1",
        active_edge=Edge.RISING,
        sample_mode=AcquisitionType.FINITE,
        samps_per_chan=total_ticks,
    )

    ci_task.in_stream.input_buf_size = total_ticks

    reader = CounterReader(ci_task.in_stream)
    reader.read_all_avail_samp = True

    ci_task.start()

    return (ci_task, reader)


def show_daq_data(ci_task: object, reader: object):
    count_array = np.zeros(total_row_acq, dtype=np.uint32)
    reader.read_many_sample_uint32(
        count_array, number_of_samples_per_channel=total_row_acq, timeout=0.1
    )
    plt.plot(count_array)
    plt.grid()
    plt.show()
    # counts = np.array(ci_task.read(number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE,timeout=1.0))
    # deltas = (counts[1:]-counts[:-1])
    deltas = count_array[1:] - count_array[:-1]
    plt.plot([0, total_row_acq], [0, total_row_acq], "r--")
    plt.plot(deltas, "k", alpha=0.5)
    plt.plot(count_array)
    plt.grid()
    plt.title("Skipped frames")
    plt.xlabel("Encoder ticks")
    plt.ylabel("Images captured")
    plt.show()
    # print(f'pulse widths (msec): {deltas}')
    ci_task.stop()
    ci_task.close()


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
    if crisp_state is not "F":
        print("CRISP not locked")

    # configure camera object
    camera = ACA2040(exp_time=EXPOSURE_TIME_US)
    camera.set_roi_zones(num_zones)

    ci_task, reader = daq_config(total_row_acq)

    # initiate scan and data acquisition
    scan(stage, mid_point=mid_point, scan_range=scan_range, num_pix=total_row_acq)
    camera.acquire(path, dirname, num_zones, total_row_acq)
    show_daq_data(ci_task, reader)

    params = {
        "total_reconstructions": num_zones,
        "total_overlap_fovs": scan_range_factor,
        "scan_midpoint": mid_point,
        "scan_range": scan_range,
    }

    fname = os.path.join(path, dirname + "_params.json")

    with open(fname, "w") as file:
        file.write(json.dumps(params))
