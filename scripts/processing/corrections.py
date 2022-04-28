import os
import math
import json
import napari
import warnings
import numpy as np
import tifffile as tf

from matplotlib import pyplot as plt
from numpy import ndarray


class Correction:
    """Post-processing methods to correct image acquisitions"""

    def __init__(self, img_arr: ndarray):
        if img_arr.dtype not in (np.uint8, np.uint16):
            print(f"Image has unsuported data type {img_arr.dtype}")
            raise TypeError

        self.img_arr = img_arr.astype(np.float64)

        # for easier processing, break image stack into list
        self.proc_arr = [self.img_arr[i] for i in range(self.img_arr.shape[0])]

        # initialize for when layers are cropped and reassembled
        self.crop_arr = None

    def row_shift(self, plot: bool = False):
        for i in range(int(len(self.proc_arr) / 2)):
            # subtract corresponding image slices for reference
            subtraction = self.proc_arr[i] - self.proc_arr[-i - 1]

            err_baseline = np.sqrt(np.sum(np.square(subtraction)))

            # shift images by a fraction of original shape
            shift_y = math.trunc(self.img_arr.shape[1] / 10)

            err_y_down = np.empty((shift_y), dtype=np.float64)
            err_y_up = np.empty((shift_y), dtype=np.float64)

            err_y_down[0] = err_baseline
            err_y_up[0] = err_baseline

            # y-axis shift-down
            for r in range(1, shift_y):
                # subtract pixel values from first and last slices
                sub = self.proc_arr[i][:-r] - self.proc_arr[-i - 1][r:]
                err_y_down[r] = np.sqrt(np.sum(np.square(sub)))

            # y-axis shift-up
            for r in range(1, shift_y):
                # subtract pixel values from first and last slices
                sub = self.proc_arr[i][r:] - self.proc_arr[-i - 1][:-r]
                err_y_up[r] = np.sqrt(np.sum(np.square(sub)))

            vertex_down = np.amin(err_y_down)
            vertex_up = np.amin(err_y_up)

            if vertex_down < vertex_up:
                err_factor_y = np.where(err_y_down == vertex_down)[0][0]
                # correction_y = img[i][:-err_factor_y] - img[-i-1][err_factor_y:]
                self.proc_arr[i] = self.proc_arr[i][:-err_factor_y]
                self.proc_arr[-i - 1] = self.proc_arr[-i - 1][err_factor_y:]
                print(
                    f"Remove {err_factor_y} rows from the bottom of plane {i} and top of plane {len(self.proc_arr) -i -1}"
                )
            else:
                err_factor_y = np.where(err_y_up == vertex_up)[0][0]
                # correction_y = img[i][err_factor_y:] - img[-i-1][:-err_factor_y]
                self.proc_arr[i] = self.proc_arr[i][err_factor_y:]
                self.proc_arr[-i - 1] = self.proc_arr[-i - 1][:-err_factor_y]
                print(
                    f"Remove {err_factor_y} rows from the top of plane {i} and bottom of plane {len(self.proc_arr) -i -1}"
                )

        if plot:
            err_y = np.append(np.flip(err_y_down), err_y_up[1:])

            fig = plt.figure()
            ax = fig.add_axes([0, 0, 1, 1])
            ax.plot(np.linspace(-shift_y, shift_y - 1, num=shift_y * 2 - 1), err_y)
            fig.savefig("error_y.jpg", bbox_inches="tight")

    def col_shift(self, plot: bool = False):
        for i in range(int(len(self.proc_arr) / 2)):
            # subtract corresponding image slices for reference
            subtraction = self.proc_arr[i] - self.proc_arr[-i - 1]

            err_baseline = np.sqrt(np.sum(np.square(subtraction)))

            shift_x = math.trunc(self.img_arr.shape[2] / 10)

            err_x_left = np.empty((shift_x), dtype=np.float64)
            err_x_right = np.empty((shift_x), dtype=np.float64)

            err_x_left[0] = err_baseline
            err_x_right[0] = err_baseline

            # x-axis shift-right
            for c in range(1, shift_x):
                # subtract pixel values from first and last slices
                sub = self.proc_arr[i][:, c:] - self.proc_arr[-i - 1][:, :-c]
                err_x_right[c] = np.sqrt(np.sum(np.square(sub)))

            # x-axis shift-left
            for c in range(1, shift_x):
                # subtract pixel values from first and last slices
                sub = self.proc_arr[i][:, :-c] - self.proc_arr[-i - 1][:, c:]
                err_x_left[c] = np.sqrt(np.sum(np.square(sub)))

            vertex_right = np.amin(err_x_right)
            vertex_left = np.amin(err_x_left)

            if vertex_right < vertex_left:
                err_factor_x = np.where(err_x_right == vertex_right)[0][0]
                # correction_x = img[i][:, err_factor_x:] - img[-i-1][:, :-err_factor_x]
                self.proc_arr[i] = self.proc_arr[i][:, err_factor_x:]
                self.proc_arr[-i - 1] = self.proc_arr[-i - 1][:, :-err_factor_x]
                print(
                    f"Remove {err_factor_x} cols from the left of plane {i} and right of plane {len(self.proc_arr) -i -1}"
                )
            else:
                err_factor_x = np.where(err_x_left == vertex_left)[0][0]
                # correction_x = img[i][:, :-err_factor_x] - img[-i-1][:, err_factor_x:]
                self.proc_arr[i] = self.proc_arr[i][:, :-err_factor_x]
                self.proc_arr[-i - 1] = self.proc_arr[-i - 1][:, err_factor_x:]
                print(
                    f"Remove {err_factor_x} cols from the right of plane {i} and left of plane {len(self.proc_arr) -i -1}"
                )

        if plot:
            err_x = np.append(np.flip(err_x_right), err_x_left[1:])

            fig = plt.figure()
            ax = fig.add_axes([0, 0, 1, 1])
            ax.plot(np.linspace(-shift_x, shift_x - 1, num=shift_x * 2 - 1), err_x)
            fig.savefig("error_x.jpg", bbox_inches="tight")

    def crop(self):
        shape = list(self.proc_arr[0].shape)

        for i in self.proc_arr:
            if i.shape[0] < shape[0]:
                shape[0] = i.shape[0]
            if i.shape[1] < shape[1]:
                shape[1] = i.shape[1]

        for i in range(len(self.proc_arr)):
            if self.proc_arr[i].shape[0] > shape[0]:
                diff = self.proc_arr[i].shape[0] - shape[0]

                if diff % 2:
                    self.proc_arr[i] = self.proc_arr[i][
                        int(diff / 2) + 1 : int(-diff / 2)
                    ]
                else:
                    self.proc_arr[i] = self.proc_arr[i][int(diff / 2) : int(-diff / 2)]

            if self.proc_arr[i].shape[1] > shape[1]:
                diff = self.proc_arr[i].shape[1] - shape[1]

                if diff % 2:
                    self.proc_arr[i] = self.proc_arr[i][
                        :, int(diff / 2) + 1 : int(-diff / 2)
                    ]
                else:
                    self.proc_arr[i] = self.proc_arr[i][
                        :, int(diff / 2) : int(-diff / 2)
                    ]

        self.crop_arr = np.stack(self.proc_arr, axis=0)

    def apply_full_correction(self):
        self.row_shift()
        self.col_shift()
        self.crop()

    def apply_col_filter(self):
        """Remove interference from imaging planes

        Assumes that the filter values file is located in same directory
        """
        if os.path.exists(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "filter_vals.json"
            )
        ):
            with open("scripts/processing/filter_vals.json") as file:
                filters = json.loads(file.read())

            col_filter_vals = filters[str(self.img_arr.shape[0])]
            col_filter_vals = np.multiply(
                col_filter_vals, (1 / np.amin(col_filter_vals))
            )
            for p in range(self.img_arr.shape[0]):
                for r in range(self.img_arr.shape[1]):
                    self.img_arr[p][r] = self.img_arr[p][r] / col_filter_vals[p]
        else:
            warnings.warn("Missing filter values file!")

    def show(self):
        viewer = napari.Viewer()

        viewer.dims.axis_labels = ("z", "y", "x")
        viewer.add_image(self.img_arr, name="raw", visible=False)
        viewer.add_image(self.crop_arr, name="processed")

        napari.run()
