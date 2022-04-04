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

from asistage import MS2000
from pypylon import pylon, genicam
from datetime import datetime
from threading import Thread
from PIL import Image


def camera_setup():
    try:
        # grab camera
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.Open()

        camera.PixelFormat = "Mono12"

        # exposure time range: 20.0 to 10000000.0 us
        camera.ExposureTime = 3642.0

        # sensor pixel dimensions: 2048 x 1544
        camera.Width = camera.Width.Max
        camera.OffsetX.SetValue(0)
        camera.Height = camera.Height.Min
        camera.OffsetY.SetValue(0)

        # camera.ROIZoneSelector.SetValue("Zone0")
        # camera.ROIZoneOffset.SetValue(0)
        # camera.ROIZoneSize.SetValue(4)
        # mode = camera.ROIZoneMode

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

def record_images(camera: object, stage: object, path: str, num_images: int = 0, save: bool = False):
    stack = np.empty((0, 2064), float)

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
                if save:
                    img.AttachGrabResultBuffer(grab_result)
                    filename = os.path.join(path, f"img_{img_counter}.jpeg")
                    save_image(img, filename)
                else:
                    stack = np.append(stack, grab_result.Array, axis=0) 
                img_counter += 1
            else:
                print("Error: ", grab_result.ErrorCode, grab_result.ErrorDescription)
            grab_result.Release()
    except genicam.GenericException as e:
        print("Exception: ", e)
    finally:
        if not save:
            save_image_array(stack, os.path.join(path, "img_reconstruction.tif"))
        # stage.send_command("TTL X=0")
        stage.close()
        camera.Close()
        print("FINISHED")

def scan(stage: object, start: float, stop: float, vel: float = 0.1):
    # reposition stage axes
    # stage.move(x=0, y=0, z=0, f=0)

    # set TTL output to pulse at constant velocity x-axis movement
    stage.ttl(x=0, y=3)

    # set xy velocity to 0.1 mm/s
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

    record = Thread(target=record_images, args=(camera, stage, path, 1544, False,))
    record.start()

    scan(stage, start=-0.75, stop=0.75, vel=0.1)

    # one thread per inch setting for coarse stage CCA X=18
