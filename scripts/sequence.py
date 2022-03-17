# ===============================================================================
#    Combine camera and stage logic.
# ===============================================================================

from asi_model import MS2000
from pypylon import pylon


# create MS-2000 serial interface
stage = MS2000("COM3", 115200)

# stage.move(0, 0, 0)
# stage.move(0, 0, -100)

# stage.moverel(10000, 0)
# stage.wait_for_device()
# stage.moverel(0, 10000)
# stage.wait_for_device()
# stage.moverel(-10000, 0)
# stage.wait_for_device()
# stage.moverel(0, -10000)
# stage.wait_for_device()

# check ring buffer mode (F=1 => standard TTL trigger mode)
stage.send_command("RM F?")
stage.read_response()

# clear the ring buffer
stage.send_command("RM X=0")

for step in range(0, 10000, 200):
    # stage.load_buffer(step, step, -1*step)
    stage.send_command(f"MOVE Z={-1*step}")
    stage.read_response()
    stage.wait_for_device()

# for i in range(50):
#     stage.send_command("LD Z?")
#     stage.read_response()

    # stage.send_command("RM")
    # stage.read_response()

    # stage.wait_for_device()

# stage.move(0, 0, 0)

# move piezo stage to 0 position
# stage.send_command("MOVE X=0 Y=0 Z=0 F=0")

# load the buffer (units are 1/10 um)
for step in range(0, 20000, 200):
    # for linear z, negative values move closer to sample
    command = f"LD X={step} Y={step} Z={-1*step}"
    stage.send_command(command)
    next_pos = stage.send_command("LD Z?")

# stage.transmit("RM Y=4 Z=0")

# set TTL
stage.send_command("TTL X=1")

# camera discovery
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

camera.LineSelector.SetValue("Line2")
camera.LineSource.SetValue("ExposureActive")
camera.LineMinimumOutputPulseWidth.SetValue(10.0) # signal pulse width [us]

numberOfImagesToGrab = 100
camera.StartGrabbingMax(numberOfImagesToGrab)

while camera.IsGrabbing():
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    if grabResult.GrabSucceeded():
        # access image data
        print("SizeX: ", grabResult.Width)
        print("SizeY: ", grabResult.Height)
        img = grabResult.Array
        print("Gray value of first pixel: ", img[0, 0])

    grabResult.Release()

# housekeeping
stage.send_command("TTL X=0")
stage.close()

camera.Close()