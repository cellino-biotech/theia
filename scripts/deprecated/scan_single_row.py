# ===============================================================================
#    Combine camera and stage logic
#
#    Imaging one pixel row at 3642.0 us exposure time results in 269.0 fps
# 
#    To reconstruct an image spanning one FOV:
#       scan_dist_mm = 1544 * pixel_size_um / 1000 (pixel_size_um = 0.35)
#       scan_speed_mm-s = pixel_size_um / 1000 * fps
# ===============================================================================

import os
import time
import platform
import numpy as np

from pypylon import pylon, genicam
from datetime import datetime
from threading import Thread
from PIL import Image
from asi.asistage import MS2000


def camera_setup():
    try:
        # grab camera
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.Open()

        # reset ROIs
        for i in range(8):
            camera.ROIZoneSelector.SetValue(f"Zone{i}")
            camera.ROIZoneMode.SetValue("Off")

        camera.PixelFormat = "Mono12"

        # exposure time range: 20.0 to 10000000.0 us
        camera.ExposureTime = 3642.0

        # sensor pixel dimensions: 2048 x 1544
        camera.Width = camera.Width.Max
        camera.OffsetX.SetValue(0)
        camera.Height = camera.Height.Min
        camera.OffsetY.SetValue(0)

        # number of buffers allocated for acquisitions
        camera.MaxNumBuffer = 5

        return camera
    except genicam.GenericException as e:
        print("Exception: ", e)
        return None

def save_image(img: object, filename: str):
    if platform.system() == "Windows":
        ipo = pylon.ImagePersistenceOptions()
        quality = 90
        ipo.SetQuality(quality)

        img.Save(pylon.ImageFileFormat_Jpeg, filename, ipo)

def save_image_array(img_array: object, filename: str):
    img = Image.fromarray(img_array)
    img.save(filename)

def record_images(camera: object, stage: object, path: str, num_images: int = 0, reconstruct: bool = False):
    reconstruction = np.empty((0, 2064), np.uint16)

    # use GPIO as trigger
    camera.LineSelector.SetValue("Line3")
    camera.LineMode.SetValue("Input")

    # initialize status
    status = camera.LineStatus.GetValue()

    img = pylon.PylonImage()
    img_counter = 0

    # poll line to check for change in status
    while camera.LineStatus.GetValue() == status:
        time.sleep(0.01)

    try:
        camera.StartGrabbingMax(num_images)

        while camera.IsGrabbing():
            grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grab_result.GrabSucceeded():
                if reconstruct:
                    reconstruction = np.append(reconstruction, grab_result.Array, axis=0)
                else:
                    img.AttachGrabResultBuffer(grab_result)
                    filename = os.path.join(path, f"img_{img_counter}.jpeg")
                    save_image(img, filename)
                    img_counter += 1
            else:
                print("Error: ", grab_result.ErrorCode, grab_result.ErrorDescription)
            grab_result.Release()
    except genicam.GenericException as e:
        print("Exception: ", e)
    finally:
        if reconstruct:
            save_image_array(reconstruction, os.path.join(path, "img_reconstruction.tif"))
        stage.close()
        camera.Close()
        print("FINISHED")

def scan(stage: object, start: float, stop: float, vel: float = 0.1):
    # set TTL output to pulse at constant velocity x-axis movement
    stage.ttl(y=3)

    stage.set_speed(x=vel, y=vel)

    stage.scan_y_axis(start=start, stop=stop)


if __name__ == "__main__":
    now = datetime.now()
    dir = now.strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join("C:/Users/lukas/Data", dir)
    os.mkdir(path)

    # create MS-2000 serial interface
    stage = MS2000("COM3", 115200)

    camera = camera_setup()

    record = Thread(target=record_images, args=(camera, stage, path, 1544, True,))
    record.start()

    scan(stage, start=-0.75, stop=0.75, vel=0.09415)
