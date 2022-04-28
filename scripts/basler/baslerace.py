import os
import math
import numpy as np
import tifffile as tf

from pypylon import pylon, genicam
from pypylon.pylon import InstantCamera, TlFactory


class ACA2040(InstantCamera):
    """Camera model"""

    def __init__(
        self,
        pix_format: str = "Mono12p",
        exp_time: int = 100,
        frame_width: int = 2064,
        num_buffers: int = 15,
    ):
        try:
            super().__init__(TlFactory.GetInstance().CreateFirstDevice())

            # open camera port
            self.Open()

            # allocate buffers for acquisitions
            self.MaxNumBuffer.SetValue(num_buffers)

            self.AcquisitionMode.SetValue("Continuous")

            # Mono12p adds padding zeros to data bytes
            self.PixelFormat.SetValue(pix_format)

            # exposure time in micro-seconds
            self.ExposureTime.SetValue(exp_time)

            # offset must be zero if max width
            self.Width.SetValue(frame_width)
            self.OffsetX.SetValue(0)

        except genicam.GenericException as e:
            if "Device is exlusively opened by another client" in e:
                print("Camera is opened in another program!")
            else:
                print("Exception: ", e)

    @staticmethod
    def save_image_array(img_array: object, filename: str):
        # add an empty color channel
        img_array = np.expand_dims(img_array, axis=0)

        # rearrange data for multidimensional tiff standard
        img_array = np.transpose(img_array, axes=[1, 0, 2, 3])

        tf.imwrite(filename, img_array, imagej=True)

    def set_trigger(
        self,
        line: int = 1,
        activation: str = "RisingEdge",
        selector: str = "FrameStart",
    ):
        self.TriggerSelector.SetValue(selector)
        self.TriggerActivation.SetValue(activation)
        self.TriggerSource.SetValue(f"Line{line}")
        self.TriggerMode.SetValue("On")

    def digital_io_control(
        self,
        line: int = 2,
        mode: str = "Input",
        source: str = "ExposureActive",
        invert: bool = False,
        pulse_width: float = 10.0,
        debounce_time: float = 0.0,
    ):
        self.LineSelector.SetValue(f"Line{line}")

        # opto-isolated line modes cannot be changed
        if line not in (1, 2):
            self.LineMode.SetValue(mode)

        if line != 1 and self.LineMode.GetValue() == "Output":
            # line source triggers the signal
            self.LineSource.SetValue(source)

            # pulse width in micro-seconds
            self.LineMinimumOutputPulseWidth.SetValue(pulse_width)
        else:
            # debounce time in micro-seconds
            self.LineDebouncerTime.SetValue(debounce_time)

        self.LineInverter.SetValue(invert)

    def reset_roi_zones(self):
        if genicam.IsWritable(self.ROIZoneMode):
            for i in range(8):
                self.ROIZoneSelector.SetValue(f"Zone{i}")
                self.ROIZoneMode.SetValue("Off")

        if genicam.IsWritable(self.OffsetY):
            # reset camera to full FOV
            self.OffsetY.SetValue(0)
            self.Height.SetValue(self.Height.Max)

    def set_roi_zones(self, num_zones: int = 3):
        # camera remembers previous settings
        self.reset_roi_zones()

        zone_spacing = math.trunc((self.Height.Max - 4) / (num_zones - 1))
        zone_offset = 0

        for i in range(num_zones):
            self.ROIZoneSelector.SetValue(f"Zone{i}")
            try:
                self.ROIZoneOffset.SetValue(zone_offset)
            except genicam.OutOfRangeException:
                # camera offset must be divisible by minimum zone pix height
                adjusted_offset = zone_offset
                while adjusted_offset % 4:
                    adjusted_offset -= 1
                self.ROIZoneOffset.SetValue(adjusted_offset)
            self.ROIZoneSize.SetValue(4)
            self.ROIZoneMode.SetValue("On")

            zone_offset += zone_spacing

    def acquire(
        self,
        path: str,
        dirname: str,
        num_zones: int = 3,
        total_row_acq: int = 1544,
        frame_width: int = 2064,
    ) -> object:
        # initialize imaging data array
        reconstruction = np.empty((num_zones, total_row_acq, frame_width), np.uint16)

        # initialize counter to track acquisitions
        acq_counter = 0

        try:
            self.StartGrabbingMax(total_row_acq, pylon.GrabStrategy_OneByOne)

            while self.IsGrabbing():
                # use timeout of 2000ms (must be greater than exposure time)
                grab_result = self.RetrieveResult(
                    5000, pylon.TimeoutHandling_ThrowException
                )

                if grab_result.GrabSucceeded():
                    for i in range(num_zones):
                        reconstruction[i][acq_counter] = grab_result.Array[
                            i * 4
                        ].reshape((1, 2064))
                    acq_counter += 1
                else:
                    print(
                        "Error: ", grab_result.ErrorCode, grab_result.ErrorDescription
                    )
                grab_result.Release()
        except genicam.GenericException as e:
            print(e)
        finally:
            self.StopGrabbing()

            print(f"total images requested: {total_row_acq}")
            print(f"total images recorded: {acq_counter}")

            overlap = []

            for i in range(num_zones):
                self.ROIZoneSelector.SetValue(f"Zone{i}")
                offset = self.ROIZoneOffset.GetValue()

                start = self.Height.Max - offset
                stop = total_row_acq - (self.Height.Max - start)

                overlap.append(reconstruction[i, start:stop, :])

            self.save_image_array(
                np.stack(reconstruction, axis=0),
                os.path.join(path, dirname + "_raw.tif"),
            )

            self.save_image_array(
                np.stack(overlap, axis=0),
                os.path.join(path, dirname + "_overlap.tif"),
            )

            self.close()

    def close(self):
        self.reset_roi_zones()

        # deactivate triggering
        self.TriggerMode.SetValue("Off")

        self.Close()
