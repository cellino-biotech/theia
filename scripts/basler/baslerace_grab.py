# ===============================================================================
#    Grab and process images from Basler cameras
# ===============================================================================

from pypylon import pylon

# camera discovery
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

camera.TriggerMode.SetValue("On")
camera.TriggerSelector.SetValue("FrameStart")

camera.LineSelector.SetValue("Line2")
camera.LineSource.SetValue("ExposureActive")
camera.LineMinimumOutputPulseWidth.SetValue(100.0) # signal pulse width [us]

numberOfImagesToGrab = 100
camera.StartGrabbingMax(numberOfImagesToGrab)

while camera.IsGrabbing():
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    if grabResult.GrabSucceeded():
        # Access the image data.
        print("SizeX: ", grabResult.Width)
        print("SizeY: ", grabResult.Height)
        img = grabResult.Array
        print("Gray value of first pixel: ", img[0, 0])

    grabResult.Release()
camera.Close()