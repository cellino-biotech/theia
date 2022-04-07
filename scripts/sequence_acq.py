# ===============================================================================
#    Sequence acquisitions can be used to create z-stacks
#    
#    Requires TTL signal from camera to stage
#    Stage moves to the next position in ring buffer at TTL signal
# ===============================================================================

import os
import math
import platform

from asistage import MS2000
from pypylon import pylon
from pypylon import genicam


def config_stage(stage: object, zstack_range_um: int, num_zslices: int):
    # reset piezo axis
    stage.move_axis("F", 0)

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

    # ASI units are 1/10 um
    stop = math.trunc(zstack_range_um / 10 / 2)
    start = -1 * stop
    step = math.trunc(zstack_range_um / num_zslices)

    # load the buffer
    for val in range(start, stop, step):
        # for linear z, negative values move closer to sample
        command = f"LD F={-1*val}"
        stage.send_command(command)
        # stage.read_response()

    # set TTL
    stage.send_command("TTL X=1")

def config_camera():
    try:
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.Open()

        camera.TriggerMode.SetValue("On")
        camera.TriggerSelector.SetValue("FrameStart")

        camera.LineSelector.SetValue("Line2")
        camera.LineSource.SetValue("ExposureActive")
        camera.LineMinimumOutputPulseWidth.SetValue(100.0) # signal pulse width [us]

        return camera
    except genicam.GenericException:
        raise

def sequence(camera: object, num_zslices: int):
    try:
        # image_window = pylon.PylonImageWindow()
        # image_window.Create(1)

        img = pylon.PylonImage()
        tlf = pylon.TlFactory.GetInstance()

        numberOfImagesToGrab = num_zslices
        camera.StartGrabbingMax(numberOfImagesToGrab, pylon.GrabStrategy_LatestImageOnly)

        while camera.IsGrabbing():
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grabResult.GrabSucceeded():
                # image_window.SetImage(grabResult)
                # image_window.Show()
                img.AttachGrabResultBuffer(grabResult)
            else:
                print(grabResult.ErrorCode)

            if platform.system() == 'Windows':
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
    except genicam.GenericException:
        raise
    finally:
        stage.send_command("TTL X=0")
        stage.close()
        camera.Close()
        print("FINISHED!")

if __name__ == "__main__":
    # create MS-2000 serial interface
    stage = MS2000("COM3", 115200)

    config_stage(stage, zstack_range_um=1000, num_zslices=10)

    camera = config_camera()

    sequence(camera, )
