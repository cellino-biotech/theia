# ===============================================================================
#    Combine camera and stage logic
# ===============================================================================

import os
import platform

from asistage import MS2000
from pypylon import pylon
from pypylon import genicam
from datetime import datetime


NUM_IMAGES = 50
EXIT_CODE = 0

# create MS-2000 serial interface
stage = MS2000("COM3", 115200)

# reposition stage axes
# NOTE: some commands must be executed twice?
stage.move(x=0, y=0, z=-2358, f=0)
stage.move(x=0, y=0, z=-2358, f=0)

# query ring buffer configuration
stage.send_command("RM Y?")
buf_config = stage.read_response()

# buffer config must read Y=15
if "Y=15" not in buf_config:
    # enable all axes to move based on ring buffer values
    stage.set_ring_buffer(15)
    # save configuration to flash memory
    stage.save_settings()

# check ring buffer mode (F=1 => standard TTL trigger mode)
stage.send_command("RM F?")
buf_mode = stage.read_response()

if "F=1" not in buf_mode:
    stage.send_command("RM F=1")

# clear the ring buffer
stage.send_command("RM X=0")

# configure TTL
stage.send_command("TTL X=1")

try:
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    camera.LineSelector.SetValue("Line3")
    camera.LineMode.SetValue("Input")
    status = camera.LineStatus.GetValue()

    camera.PixelFormat = "Mono8"

    # sensor pixel dimensions: 2048 x 1544
    camera.Width = camera.Width.Max
    camera.Height = camera.Height.Max
    # camera.Height = camera.Height.Min

    # set the y-axis offset to position strip at center
    if genicam.IsWritable(camera.OffsetY):
        # camera.OffsetY = 772
        camera.OffsetY = camera.OffsetY.Min

    # number of buffers allocated for acquisitions
    camera.MaxNumBuffer = 5

    img = pylon.PylonImage()

    img_counter = 0

    now = datetime.now()
    dir = now.strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join("C:/Users/lukas/Data", dir)
    os.mkdir(path)

    camera.StartGrabbingMax(NUM_IMAGES)

    while camera.IsGrabbing():
        grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        if grab_result.GrabSucceeded():
            img_arr = grab_result.Array

            img.AttachGrabResultBuffer(grab_result)

            if platform.system() == 'Windows':
                ipo = pylon.ImagePersistenceOptions()
                quality = 90
                ipo.SetQuality(quality)

                filename = os.path.join(path, f"img_{img_counter}.jpeg")

                while os.path.exists(filename):
                    img_counter += 1
                    filename = os.path.join(path, f"img_{img_counter}.jpeg")

                img.Save(pylon.ImageFileFormat_Jpeg, filename, ipo)
        else:
            print("Error: ", grab_result.ErrorCode, grab_result.ErrorDescription)
        grab_result.Release()
except genicam.GenericException as e:
    print("Exception: ", e)
finally:
    stage.send_command("TTL X=0")
    stage.close()
    camera.Close()
    print("FINISHED")
