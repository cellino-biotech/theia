# ===============================================================================
#    Combine camera and stage logic
# ===============================================================================

import os
import time
import platform

from asistage import MS2000
from pypylon import pylon
from pypylon import genicam


NEW_CONFIG = True

# create MS-2000 serial interface
stage = MS2000("COM3", 115200)

stage.move_axis("F", 0)
stage.move_axis("F", 0)

if NEW_CONFIG:
    # enable all axes to move based on values stored in ring buffer
    stage.set_ring_buffer(15)

    # query ring buffer configuration
    stage.send_command("RM Y?")
    stage.read_response()

# check ring buffer mode (F=1 => standard TTL trigger mode)
stage.send_command("RM F?")
stage.read_response()

# clear the ring buffer
stage.send_command("RM X=0")

# load the buffer (units are 1/10 um)
for step in range(-500, 500, 20):
    # for linear z, negative values move closer to sample
    command = f"LD F={-1*step}"
    stage.send_command(command)
    # stage.read_response()

# set TTL
stage.send_command("TTL X=1")

try:
    # image_window = pylon.PylonImageWindow()
    # image_window.Create(1)

    img = pylon.PylonImage()
    tlf = pylon.TlFactory.GetInstance()

    # camera discovery
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    camera.TriggerMode.SetValue("On")
    camera.TriggerSelector.SetValue("FrameStart")

    camera.LineSelector.SetValue("Line2")
    camera.LineSource.SetValue("ExposureActive")
    camera.LineMinimumOutputPulseWidth.SetValue(100.0) # signal pulse width [us]

    numberOfImagesToGrab = 50
    camera.StartGrabbingMax(numberOfImagesToGrab, pylon.GrabStrategy_LatestImageOnly)

    start = time.time()
    while camera.IsGrabbing():
        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        if grabResult.GrabSucceeded():
            # image_window.SetImage(grabResult)
            # image_window.Show()
            img.AttachGrabResultBuffer(grabResult)
        # else:
            # print(grabResult.ErrorCode)

        if platform.system() == 'Windows':
            # The JPEG format that is used here supports adjusting the image
            # quality (100 -> best quality, 0 -> poor quality).
            ipo = pylon.ImagePersistenceOptions()
            quality = 90
            ipo.SetQuality(quality)

            filename = "saved_pypylon_img_%d.jpeg" % quality
            while os.path.exists(filename):
                filename = filename.split(".")[0] + "x" + ".jpeg"
            img.Save(pylon.ImageFileFormat_Jpeg, filename, ipo)
        else:
            filename = "saved_pypylon_img_%d.png"
            while os.path.exists(filename):
                filename = filename.split(".")[0] + "x" + ".jpeg"
            img.Save(pylon.ImageFileFormat_Png, filename)

        grabResult.Release()
        img.Release()
        # time.sleep(1)
except genicam.GenericException:
    raise
finally:
    print(time.time() - start)
    # housekeeping
    stage.send_command("TTL X=0")
    stage.close()

    camera.Close()
    print("FINISHED!")