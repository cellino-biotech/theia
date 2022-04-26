# ===============================================================================
#    Use XY encoder output signals to drive camera acquisition during scan
# ===============================================================================

import os
import math
import json
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime
from asi.asistage import MS2000

import nidaqmx
from nidaqmx.constants import (AcquisitionType, CountDirection, Edge, READ_ALL_AVAILABLE, TaskMode, TriggerType)


# explicit constants
SENSOR_WIDTH_PIX  = 2064
SENSOR_HEIGHT_PIX = 1544
PIX_SIZE_MM       = 0.35E-3 # determined from ImageJ
EXPOSURE_TIME_US  = 100     # given max light intensity
FPS_MAX           = 635

# inferred constants
FOV_HEIGHT_MM = SENSOR_HEIGHT_PIX * PIX_SIZE_MM


def record_images(camera: object, stage: object, path: str, dirname: str, num_zones: int = 3, total_row_acq: int = 1544):
    # initialize data array
    reconstruction = np.empty((num_zones, total_row_acq, SENSOR_WIDTH_PIX), np.uint16)

    try:
        ci_task = nidaqmx.Task()
        channel = ci_task.ci_channels.add_ci_count_edges_chan('Dev1/ctr0',
            initial_count=0, edge=Edge.FALLING, count_direction=CountDirection.COUNT_UP)
        channel.ci_count_edges_term = '/Dev1/20MHzTimebase'# 'PFI0'

        ci_task.timing.cfg_samp_clk_timing(rate=100000, source='PFI0', active_edge=Edge.FALLING,
            sample_mode=AcquisitionType.FINITE, samps_per_chan=1000)
        ci_task.start()
        
        # use the first-in-first-out processing approach
        camera.StartGrabbingMax(total_row_acq, pylon.GrabStrategy_OneByOne)

        counter = 0

        while camera.IsGrabbing():
            # use timeout of 2000ms (must be greater than exposure time)
            grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            # try to get actual position of the acquired image

            if grab_result.GrabSucceeded():
                for i in range(num_zones):
                    reconstruction[i][counter] = grab_result.Array[i*4].reshape((1, 2064))
                counter += 1
            else:
                print("Error: ", grab_result.ErrorCode, grab_result.ErrorDescription)
            grab_result.Release()
    except genicam.GenericException as e:
        print(e)
    finally:
        print(f"total images requested: {total_row_acq}")
        print(f"total images recorded: {counter}")
        camera.StopGrabbing()

        counts = np.array(ci_task.read(number_of_samples_per_channel=1000))
        deltas = 1000*((counts[1:]-counts[:-1])/2.0E7)
        plt.hist(deltas, bins=50)
        plt.xlabel('encoder period (msec)')
        plt.title(f'mean = {np.mean(deltas):0.1f}, sd={np.std(deltas):0.1f}, min={np.min(deltas):0.1f}, max={np.max(deltas):0.1f}')
        plt.show()
        #print(f'pulse widths (msec): {deltas}')
        ci_task.close()

        layer_adjustments = {}
        
        overlap = []

        for i in range(num_zones):
            camera.ROIZoneSelector.SetValue(f"Zone{i}")
            offset = camera.ROIZoneOffset.GetValue()

            start = SENSOR_HEIGHT_PIX - offset
            stop = total_row_acq - (SENSOR_HEIGHT_PIX - start)

            overlap.append(reconstruction[i, start:stop, :])

            layer_adjustments[f"{i}"] = {
                "offset": offset, 
                "start": start,
                "stop": stop
            }
        
        save_image_array(np.stack(reconstruction, axis=0), os.path.join(path, dirname + "_raw.tif"))
        save_image_array(np.stack(overlap, axis=0), os.path.join(path, dirname + "_overlap.tif"))

        reset_roi_zones(camera)

        # deactivate triggering
        camera.TriggerMode.SetValue("On")
        
        camera.Close()
        stage.close()

        return layer_adjustments

def scan(stage: object, mid_point: tuple, scan_range: float, num_pix: int):
    # first move to mid-point y-value
    stage.set_speed(x=1, y=1)
    stage.move_axis("Y", mid_point[1])
    stage.wait_for_device()

    vel = PIX_SIZE_MM * FPS_MAX
    vel = 2.5
    print(f"Velocity: {vel}mm/sec")

    stage.set_speed(x=vel, y=vel)

    start = mid_point[0] - scan_range/2 - FOV_HEIGHT_MM/2

    with nidaqmx.Task() as ci_task:
        channel = ci_task.ci_channels.add_ci_count_edges_chan('Dev1/ctr0',
            initial_count=0, edge=Edge.FALLING, count_direction=CountDirection.COUNT_UP)
        channel.ci_count_edges_term = '/Dev1/20MHzTimebase'# 'PFI0'

        ci_task.timing.cfg_samp_clk_timing(rate=100000, source='PFI0', active_edge=Edge.FALLING,
            sample_mode=AcquisitionType.FINITE, samps_per_chan=num_pix)
        ci_task.start()

        stage.scan_x_axis_enc(start=start, num_pix=num_pix, enc_divide=38)

        print(f'number of pixels = {num_pix}')

        counts = np.array(ci_task.read(number_of_samples_per_channel=2000))
        deltas = 1000*((counts[1:]-counts[:-1])/2.0E7)
        plt.hist(deltas, bins=50)
        plt.xlabel('encoder period (msec)')
        plt.title(f'mean = {np.mean(deltas):0.2f}, sd={np.std(deltas):0.2f}, min={np.min(deltas):0.2f}, max={np.max(deltas):0.2f}')
        plt.grid()
        plt.show()

        vels = 0.38E-3/(deltas/1000)
        plt.plot(vels)
        plt.grid()
        plt.title('ASI stage constant velocity scan')
        plt.xlabel('tick')
        plt.ylabel('instantaneous velocity (mm/sec)')
        plt.xlim(0, len(vels))
        plt.plot([0,len(vels)], [vel, vel], 'r--')
        plt.show()
        #print(f'pulse widths (msec): {deltas}')
        ci_task.close()


if __name__ == "__main__":

    # create MS-2000 serial interface
    stage = MS2000("COM3", 115200)

    num_zones = 5 # number of z-slices
    mid_point = (0, 0)
    scan_range_factor = 1 # number of overlapping fov images

    scan_range = scan_range_factor * FOV_HEIGHT_MM

    total_row_acq = SENSOR_HEIGHT_PIX * (scan_range_factor + 1) 
    
    scan(stage, mid_point=mid_point, scan_range=scan_range, num_pix=total_row_acq)

