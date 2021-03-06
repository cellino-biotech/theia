# ===============================================================================
#    Combine camera and stage logic
#
#    To reconstruct an image spanning one FOV:
#       fov_mm = 1544 * pixel_size_mm (pixel_size_mm = 0.35E-3)
#       scan_speed_mm-s = pixel_size_mm * fps
# ===============================================================================

import os
import time
import math
import tifffile
import threading
import numpy as np

from pypylon import pylon, genicam
from datetime import datetime
from asistage import MS2000


# constants
SENSOR_WIDTH_PIX = 2064
SENSOR_HEIGHT_PIX = 1544
PIX_SIZE_MM = 0.35e-3  # determined from ImageJ
EXPOSURE_TIME_US = 1500  # given max light intensity
FPS_MAX = 635

# inferred constants
FOV_HEIGHT_MM = SENSOR_HEIGHT_PIX * PIX_SIZE_MM


def create_data_dir():
    now = datetime.now()
    dirname = now.strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join("C:\\Users\\lukas\\Data", dirname)
    os.mkdir(path)
    return (path, dirname)


def reset_roi_zones(camera: object):
    for i in range(8):
        camera.ROIZoneSelector.SetValue(f"Zone{i}")
        camera.ROIZoneMode.SetValue("Off")

    if genicam.IsWritable(camera.OffsetY):
        # reset camera to full FOV
        camera.OffsetY.SetValue(0)
        camera.Height = camera.Height.Max

    camera.AcquisitionFrameRateEnable.SetValue(False)


def set_roi_zones(camera: object, num_zones: int = 3):
    reset_roi_zones(camera)

    zone_spacing = math.trunc((SENSOR_HEIGHT_PIX - 4) / (num_zones - 1))
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

    # set framerate upper limit
    camera.AcquisitionFrameRateEnable.SetValue(True)
    camera.AcquisitionFrameRate.SetValue(FPS_MAX)


def camera_setup():
    try:
        # grab camera
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.Open()

        # Mono12p adds padding zeros to data bytes
        camera.PixelFormat = "Mono12p"

        # exposure time range: 20.0 to 10000000.0 us
        camera.ExposureTime = EXPOSURE_TIME_US

        # sensor pixel dimensions: 2064 x 1544
        camera.Width = camera.Width.Max
        camera.OffsetX.SetValue(0)

        # number of buffers allocated for acquisitions
        camera.MaxNumBuffer = 5

        # use GPIO as trigger
        # camera.LineSelector.SetValue("Line3")
        # camera.LineMode.SetValue("Input")

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


def record_images(
    camera: object,
    stage: object,
    path: str,
    dirname: str,
    num_zones: int = 3,
    total_row_acq: int = 1544,
):
    # initialize data array
    reconstruction = np.empty((num_zones, total_row_acq, SENSOR_WIDTH_PIX), np.uint16)

    # initialize status
    status = camera.LineStatus.GetValue()

    # poll line to check for change in status
    while camera.LineStatus.GetValue() == status:
        time.sleep(0.01)

    try:
        camera.StartGrabbingMax(total_row_acq)

        counter = 0

        while camera.IsGrabbing():
            grab_result = camera.RetrieveResult(
                5000, pylon.TimeoutHandling_ThrowException
            )

            if grab_result.GrabSucceeded():
                for i in range(num_zones):
                    reconstruction[i][counter] = grab_result.Array[i * 4].reshape(
                        (1, 2064)
                    )
                counter += 1
            else:
                print("Error: ", grab_result.ErrorCode, grab_result.ErrorDescription)
            grab_result.Release()

        overlap_stack = []

        for i in range(num_zones):
            camera.ROIZoneSelector.SetValue(f"Zone{i}")
            offset = camera.ROIZoneOffset.GetValue()

            start = 1544 - offset
            stop = total_row_acq - (1544 + offset)

            overlap_stack.append(reconstruction[i, start:stop, :])

        zstack = np.stack(overlap_stack, axis=0)
        save_image_array(zstack, os.path.join(path, dirname + "_stack.tif"))
    except genicam.GenericException as e:
        print("Exception: ", e)
    finally:
        # reset_roi_zones(camera)

        camera.Close()
        stage.close()
        # print("FINISHED")


def scan(stage: object, mid_point: tuple, scan_range: float):
    vel = PIX_SIZE_MM * FPS_MAX

    stage.set_speed(x=vel, y=vel)

    start = mid_point[0] - scan_range / 2 - FOV_HEIGHT_MM / 2
    stop = mid_point[0] + scan_range / 2 + FOV_HEIGHT_MM / 2

    stage.scan_x_axis(start=start, stop=stop)


if __name__ == "__main__":
    path, dirname = create_data_dir()

    # create MS-2000 serial interface
    stage = MS2000("COM3", 115200)

    camera = camera_setup()

    num_zones = 5
    mid_point = (0, 0)
    scan_range_factor = 2  # number of overlapping fov images

    scan_range = scan_range_factor * FOV_HEIGHT_MM

    total_row_acq = SENSOR_HEIGHT_PIX * (scan_range_factor + 2)

    if camera is not None:
        set_roi_zones(camera, num_zones)

        record = threading.Thread(
            target=record_images,
            args=(
                camera,
                stage,
                path,
                dirname,
                num_zones,
                total_row_acq,
            ),
        )
        record.start()

    scan(stage, mid_point=mid_point, scan_range=scan_range)

    description = input("Add description: ")

    fname = os.path.join(path, dirname + "_description.txt")

    with open(fname, "w") as f:
        f.write(f"Total image reconstructions: {num_zones}\n")
        f.write(f"Total overlapping FOVs: {scan_range_factor}\n")
        f.write(f"Scan midpoint (mm): {mid_point}\n")
        f.write(f"Scan range (mm): {scan_range}\n")

        if description:
            f.write(f"Description: {description}")

    # check if acquisitions finished
    while threading.active_count() > 1:
        time.sleep(0.2)

    print("FINISHED")
