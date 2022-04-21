# ===============================================================================
#    Use XY encoder output signals to drive camera acquisition during scan
# ===============================================================================

import os
import math
import json
import tifffile
import numpy as np

from pypylon import pylon, genicam
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

def create_data_dir():
    now = datetime.now()
    dirname = now.strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join("C:\\Users\\lukas\\Data", dirname)
    os.mkdir(path)
    return (path, dirname)

def reset_roi_zones(camera: object):
    if genicam.IsWritable(camera.ROIZoneMode):
        for i in range(8):
            camera.ROIZoneSelector.SetValue(f"Zone{i}")
            camera.ROIZoneMode.SetValue("Off")
    
    if genicam.IsWritable(camera.OffsetY):
        # reset camera to full FOV
        camera.OffsetY.SetValue(0)
        camera.Height = camera.Height.Max

def set_roi_zones(camera: object, num_zones: int = 3):
    reset_roi_zones(camera)

    zone_spacing = math.trunc((SENSOR_HEIGHT_PIX-4) / (num_zones-1))
    zone_offset = 0

    for i in range(num_zones):
        camera.ROIZoneSelector.SetValue(f"Zone{i}")
        try:
            camera.ROIZoneOffset.SetValue(zone_offset)
        except genicam.OutOfRangeException:
            # camera offset must be divisible by minimum zone pix height
            adjusted_offset = zone_offset
            while adjusted_offset % 4:
                adjusted_offset -= 1
            camera.ROIZoneOffset.SetValue(adjusted_offset)
        camera.ROIZoneSize.SetValue(4)
        camera.ROIZoneMode.SetValue("On")

        zone_offset += zone_spacing

def camera_setup():
    try:
        # grab camera
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.Open()

        camera.AcquisitionMode.SetValue('Continuous')

        # Mono12p adds padding zeros to data bytes
        camera.PixelFormat = "Mono12p"

        # exposure time range: 20.0 to 10000000.0 us
        camera.ExposureTime = EXPOSURE_TIME_US

        # sensor pixel dimensions: 2064 x 1544
        camera.Width = camera.Width.Max
        camera.OffsetX.SetValue(0)

        # number of buffers allocated for acquisitions
        camera.MaxNumBuffer = 15

        # configure IO trigger
        camera.TriggerSelector.SetValue("FrameStart")
        camera.TriggerActivation.SetValue("FallingEdge")
        camera.TriggerSource.SetValue("Line1")
        camera.TriggerMode.SetValue("On")

        return camera
    except genicam.GenericException as e:
        if "Device is exlusively opened by another client" in e:
            print("Camera is opened in another program!")
        else:
            print("Exception: ", e)
        return None

def save_image_array(img_array: object, filename: str):
    # add an empty color channel
    img_array = np.expand_dims(img_array, axis=0)

    # rearrange data for multidimensional tiff standard
    img_array = np.transpose(img_array, axes=[1, 0, 2, 3])

    tifffile.imwrite(filename, img_array, imagej=True)

def record_images(camera: object, stage: object, path: str, dirname: str, num_zones: int = 3, total_row_acq: int = 1544):
    # initialize data array
    reconstruction = np.empty((num_zones, total_row_acq, SENSOR_WIDTH_PIX), np.uint16)

    try:
        count_task = nidaqmx.Task()
        channel = count_task.ci_channels.add_ci_count_edges_chan(
            'Dev1/ctr0', initial_count=0, edge=Edge.FALLING, count_direction=CountDirection.COUNT_UP
        )
        channel.ci_count_edges_term = 'PFI0' #'/Dev1/20MHzTimebase'
        count_task.start()
        
        # use the first-in-first-out processing approach
        camera.StartGrabbingMax(total_row_acq, pylon.GrabStrategy_OneByOne)

        counter = 0

        while camera.IsGrabbing():
            # use timeout of 2000ms (must be greater than exposure time)
            grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            # try to get actual position of the acquired image
            enc_counter = count_task.read() - 1
            if counter % 100 == 0:
                print(f'count: {counter} enc: {enc_counter}')

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

        print(f'total encoder tick count: {count_task.read()}')
        count_task.close()

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
    vel = 0.1
    print(f"Velocity: {vel}mm/sec")

    stage.set_speed(x=vel, y=vel)

    start = mid_point[0] - scan_range/2 - FOV_HEIGHT_MM/2

    stage.scan_x_axis_enc(start=start, num_pix=num_pix, enc_divide=38)


if __name__ == "__main__":
    path, dirname = create_data_dir()

    # create MS-2000 serial interface
    stage = MS2000("COM3", 115200)

    camera = camera_setup()

    num_zones = 5 # number of z-slices
    mid_point = (0, 0)
    scan_range_factor = 1 # number of overlapping fov images

    scan_range = scan_range_factor * FOV_HEIGHT_MM

    total_row_acq = SENSOR_HEIGHT_PIX * (scan_range_factor + 1) 
    
    set_roi_zones(camera, num_zones)
    scan(stage, mid_point=mid_point, scan_range=scan_range, num_pix=total_row_acq)
    layer_adjustments = record_images(camera, stage, path, dirname, num_zones, total_row_acq)

    params = {
        "total_reconstructions": num_zones,
        "total_overlap_fovs": scan_range_factor,
        "scan_midpoint": mid_point,
        "scan_range": scan_range,
        "layer_adjustments": layer_adjustments
    }

    fname = os.path.join(path, dirname + "_params.json")

    with open(fname, "w") as file:
        file.write(json.dumps(params))
