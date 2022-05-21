# ===============================================================================
#    Camera control for Basler ACA2040 120um camera sensor
# ===============================================================================

import math
import warnings
import numpy as np
import tifffile as tf

from pypylon import pylon, genicam
from pypylon.pylon import InstantCamera, TlFactory
from numpy import ndarray
from nidaqmx import Task


class ACA2040:
    """Camera model"""

    def __init__(
        self,
        pix_format: str = "Mono12p",
        exposure_time_us: int = 100,
        frame_width_pix: int = 2064,
        sensor_pixel_size_mm: float = 370e-6,
        num_buffers: int = 15,
    ):
        self.sensor_width_pix = 2064
        self.sensor_height_pix = 1544
        self.fps_max = 635

        self.pix_format = pix_format
        self.exposure_time_us = exposure_time_us
        self.frame_width_pix = frame_width_pix
        self.sensor_pix_size_mm = sensor_pixel_size_mm
        self.num_buffers = num_buffers

        self.fov_height_mm = self.sensor_height_pix * self.sensor_pix_size_mm

        try:
            self.dev = InstantCamera(TlFactory.GetInstance().CreateFirstDevice())

            # open camera port
            self.dev.Open()

            # allocate buffers for acquisitions
            self.dev.MaxNumBuffer.SetValue(self.num_buffers)

            # alternative mode is "SingleFrame"
            self.dev.AcquisitionMode.SetValue("Continuous")

            # Mono12p adds padding zeros to data bytes
            self.dev.PixelFormat.SetValue(self.pix_format)

            # exposure time in micro-seconds
            self.dev.ExposureTime.SetValue(self.exposure_time_us)

            # offset must be zero if max width
            self.dev.OffsetX.SetValue(0)
            self.dev.Width.SetValue(self.frame_width_pix)

        except genicam.GenericException as e:
            if "Device is exlusively opened by another client" in e:
                print("Camera is opened in another program!")
            else:
                print("Exception: ", e)

    @staticmethod
    def save_image_array(img_arr: ndarray, fname: str):
        """Save numpy image array as 16-bit tiff file"""
        if img_arr.dtype != np.uint16:
            img_arr = img_arr.astype(np.uint16)
        tf.imwrite(fname, img_arr, imagej=True)

    @staticmethod
    def format_image_array(img_arr: ndarray) -> ndarray:
        """Add an empty color channel and rearrange axes

        Needed for saving tiff files that can be read with
        ImageJ and Napari
        """
        if img_arr.ndim < 4:
            img_arr = np.expand_dims(img_arr, axis=0)
            img_arr = np.transpose(img_arr, axes=[1, 0, 2, 3])

        return img_arr

    @staticmethod
    def illuminator(on_state: bool = True):
        """Toggle LED illuminator"""
        with Task() as task:
            task.do_channels.add_do_chan("Dev1/port0/line0")
            task.write(on_state)

    def crop_overlap_zone(self, img_arr: ndarray) -> ndarray:
        """Remove non-overlapping rows from each plane"""
        # we can infer the size of the overlapping array
        overlap_arr = np.empty(
            (
                img_arr.shape[0],
                img_arr.shape[1] - self.dev.Height.Max,
                img_arr.shape[2],
            ),
            dtype=np.uint16,
        )

        for p in range(img_arr.shape[0]):
            self.dev.ROIZoneSelector.SetValue(f"Zone{p}")
            offset = self.dev.ROIZoneOffset.GetValue()

            start = self.dev.Height.Max - offset
            stop = img_arr.shape[1] - (self.dev.Height.Max - start)

            overlap_arr[p] = img_arr[p, start:stop, :]

        return overlap_arr

    def set_trigger(
        self,
        source: str = "Line1",
        activation: str = "RisingEdge",
        selector: str = "FrameStart",
    ):
        """Set hardware trigger"""
        self.dev.TriggerSelector.SetValue(selector)
        if "Line" in source:
            self.dev.TriggerActivation.SetValue(activation)
        self.dev.TriggerSource.SetValue(source)
        self.dev.TriggerMode.SetValue("On")

    def set_io_control(
        self,
        line: int = 2,
        mode: str = "Input",
        source: str = "ExposureActive",
        invert: bool = False,
        pulse_width: float = 10.0,
        debounce_time: float = 0.0,
    ):
        """Configure camera IO lines"""
        self.dev.LineSelector.SetValue(f"Line{line}")

        # opto-isolated line modes cannot be changed
        if line not in (1, 2):
            self.dev.LineMode.SetValue(mode)

        if line != 1 and self.dev.LineMode.GetValue() == "Output":
            # line source triggers the signal
            self.dev.LineSource.SetValue(source)

            # pulse width in micro-seconds
            self.dev.LineMinimumOutputPulseWidth.SetValue(pulse_width)
        else:
            # debounce time in micro-seconds
            self.dev.LineDebouncerTime.SetValue(debounce_time)

        self.dev.LineInverter.SetValue(invert)

    def reset_roi_zones(self):
        """Turn all ROI zones Off

        These settings persist in camera memory and can affect
        future acquisitions
        """
        if genicam.IsWritable(self.dev.ROIZoneMode):
            for i in range(8):
                self.dev.ROIZoneSelector.SetValue(f"Zone{i}")
                self.dev.ROIZoneMode.SetValue("Off")

        if genicam.IsWritable(self.dev.OffsetY):
            # reset camera to full FOV
            self.dev.OffsetY.SetValue(0)
            self.dev.Height.SetValue(self.dev.Height.Max)

    def set_roi_zones(self, num_zones: int = 3):
        """Automate the creation of evenly-spaced ROI zones

        If num_zones == 1, simply set the camera height to 1 pix and
        adjust offset accordingly
        """
        # NOTE: camera remembers previous settings!
        self.reset_roi_zones()

        if num_zones > 1 and num_zones < 8:
            zone_spacing = math.trunc((self.dev.Height.Max - 4) / (num_zones - 1))
            zone_offset = 0

            for i in range(num_zones):
                self.dev.ROIZoneSelector.SetValue(f"Zone{i}")
                try:
                    self.dev.ROIZoneOffset.SetValue(zone_offset)
                except genicam.OutOfRangeException:
                    # camera offset must be divisible by minimum zone pix height
                    adjusted_offset = zone_offset
                    while adjusted_offset % 4:
                        adjusted_offset -= 1
                    self.dev.ROIZoneOffset.SetValue(adjusted_offset)
                self.dev.ROIZoneSize.SetValue(4)
                self.dev.ROIZoneMode.SetValue("On")

                zone_offset += zone_spacing
        elif num_zones == 1:
            self.dev.Height.SetValue(1)
            self.dev.OffsetY.SetValue(self.sensor_height_pix / 2)
        else:
            warnings.warn("Requested ROI zones is outside hardware configuration")

    def acquire_sequence(self, total_acqs: int, timeout: int = 5000) -> ndarray:
        # initialize imaging data array
        img_seq = np.empty(
            (total_acqs, self.dev.Height.GetValue(), self.dev.Width.GetValue()),
            np.uint16,
        )

        # initialize counter to track acquisitions
        acq_counter = 0

        try:
            self.dev.StartGrabbingMax(total_acqs, pylon.GrabStrategy_OneByOne)

            while self.dev.IsGrabbing():
                # NOTE: timeout must be greater than exposure time!
                grab_result = self.dev.RetrieveResult(
                    timeout, pylon.TimeoutHandling_ThrowException
                )

                if grab_result.GrabSucceeded():
                    img_seq[acq_counter] = grab_result.Array
                    acq_counter += 1
                else:
                    print(
                        "Error: ", grab_result.ErrorCode, grab_result.ErrorDescription
                    )
                grab_result.Release()
        except genicam.GenericException as e:
            print(e)
        finally:
            self.dev.StopGrabbing()

            return img_seq

    def acquire_stack(
        self,
        num_zones: int = 3,
        total_row_acq: int = 1544,
        frame_width: int = 2064,
        timeout: int = 5000,
    ) -> ndarray:
        """Initiate acquisition and process incoming frames in real time

        Returns a multidimensional numpy image array
        """

        # initialize imaging data array
        reconstruction = np.empty((num_zones, total_row_acq, frame_width), np.uint16)

        # initialize counter to track acquisitions
        acq_counter = 0

        try:
            self.dev.StartGrabbingMax(total_row_acq, pylon.GrabStrategy_OneByOne)

            while self.dev.IsGrabbing():
                # NOTE: timeout must be greater than exposure time!
                grab_result = self.dev.RetrieveResult(
                    timeout, pylon.TimeoutHandling_ThrowException
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
            self.dev.StopGrabbing()

            print(f"Total images requested: {total_row_acq}")
            print(f"Total images recorded: {acq_counter}")

            return reconstruction

    def close(self):
        """Housekeeping"""
        self.reset_roi_zones()

        # deactivate triggering
        self.dev.TriggerMode.SetValue("Off")

        self.dev.Close()
