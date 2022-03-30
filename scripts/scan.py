# ===============================================================================
#    Combine camera and stage logic.
# ===============================================================================

from inspect import stack
import os
import time
import platform

from asi_model import MS2000
from pypylon import pylon
from pypylon import genicam
from datetime import datetime
from threading import Thread


def camera_setup():
    try:
        # grab camera
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.Open()

        camera.PixelFormat = "Mono12"

        # exposure time range: 20.0 to 10000000.0 us
        camera.ExposureTime = 1000.0

        # sensor pixel dimensions: 2048 x 1544
        camera.Width = camera.Width.Max
        camera.Height = camera.Height.Max

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

def record_images(camera: object, stage: object, path: str, num_images: int = 0, save: bool = False):
    global stack

    stack = []

    # use GPIO as trigger
    camera.LineSelector.SetValue("Line3")
    camera.LineMode.SetValue("Input")

    # initialize status
    status = camera.LineStatus.GetValue()

    img = pylon.PylonImage()
    img_counter = 0

    # poll line to check for change in status
    while camera.LineStatus.GetValue() == status:
        time.sleep(0.1)

    try:
        camera.StartGrabbingMax(num_images)

        while camera.IsGrabbing():
            grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grab_result.GrabSucceeded():
                if save:
                    img.AttachGrabResultBuffer(grab_result)
                    filename = os.path.join(path, f"img_{img_counter}.jpeg")
                    save_image(img, filename)
                    img_counter += 1
                else:
                    stack.append(grab_result.Array)     
            else:
                print("Error: ", grab_result.ErrorCode, grab_result.ErrorDescription)
            grab_result.Release()
    except genicam.GenericException as e:
        print("Exception: ", e)
    finally:
        stage.send_command("TTL X=0")
        stage.close()
        camera.Close()
        print(stack)

def scan(stage: object):
    # reposition stage axes
    # NOTE: some commands must be executed twice?
    # stage.move(x=0, y=0, z=0, f=0)
    # stage.move(x=0, y=0, z=0, f=0)

    # configure TTL
    stage.send_command("TTL Y=3")
    stage.read_response()

    # set axis velocity to 0.1 mm/s
    stage.set_speed(x=0.1, y=0.1)

    stage.send_command("SCANR X=0 Y=1")
    stage.read_response()
    stage.send_command("SCAN X=1 Y=0 Z=0 F=0")
    stage.read_response()
    stage.send_command("SCAN")
    stage.read_response()


if __name__ == "__main__":
    now = datetime.now()
    dir = now.strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join("C:/Users/lukas/Data", dir)
    os.mkdir(path)

    # create MS-2000 serial interface
    stage = MS2000("COM3", 115200)

    # camera = camera_setup()

    # record = Thread(target=record_images, args=(camera, stage, path, 50, True,))
    # record.start()

    scan(stage)
