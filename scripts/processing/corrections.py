import math
import napari
import numpy as np
import tifffile as tf

from matplotlib import pyplot as plt


class Correction:
    """Post-processing methods to correct image acquisitions"""

    def __init__(self, fname: str):
        img = tf.imread(fname)

        if img.dtype not in (np.uint8, np.uint16):
            print(f"Image has unsuported data type {img.dtype}")
            raise TypeError

        self.img = img.astype(np.float64)

        # for easier processing, break image stack into list
        self.proc = [self.img[i] for i in range(self.img.shape[0])]

        # initialize for when layers are cropped and reassembled
        self.crop_stack = None

    def row_shift(self, plot: bool = False) -> object:
        for i in range(int(len(self.proc) / 2)):
            # subtract corresponding image slices for reference
            subtraction = self.proc[i] - self.proc[-i - 1]

            err_baseline = np.sqrt(np.sum(np.square(subtraction)))

            # shift images by a fraction of original shape
            shift_y = math.trunc(self.img.shape[1] / 10)

            err_y_down = np.empty((shift_y), dtype=np.float64)
            err_y_up = np.empty((shift_y), dtype=np.float64)

            err_y_down[0] = err_baseline
            err_y_up[0] = err_baseline

            # y-axis shift-down
            for r in range(1, shift_y):
                # subtract pixel values from first and last slices
                sub = self.proc[i][:-r] - self.proc[-i - 1][r:]
                err_y_down[r] = np.sqrt(np.sum(np.square(sub)))

            # y-axis shift-up
            for r in range(1, shift_y):
                # subtract pixel values from first and last slices
                sub = self.proc[i][r:] - self.proc[-i - 1][:-r]
                err_y_up[r] = np.sqrt(np.sum(np.square(sub)))

            vertex_down = np.amin(err_y_down)
            vertex_up = np.amin(err_y_up)

            if vertex_down < vertex_up:
                err_factor_y = np.where(err_y_down == vertex_down)[0][0]
                # correction_y = img[i][:-err_factor_y] - img[-i-1][err_factor_y:]
                self.proc[i] = self.proc[i][:-err_factor_y]
                self.proc[-i - 1] = self.proc[-i - 1][err_factor_y:]
                print(f"Shift down by {err_factor_y} rows")
            else:
                err_factor_y = np.where(err_y_up == vertex_up)[0][0]
                # correction_y = img[i][err_factor_y:] - img[-i-1][:-err_factor_y]
                self.proc[i] = self.proc[i][err_factor_y:]
                self.proc[-i - 1] = self.proc[-i - 1][:-err_factor_y]
                print(f"Shift up by {err_factor_y} rows")

        if plot:
            err_y = np.append(np.flip(err_y_down), err_y_up[1:])

            fig = plt.figure()
            ax = fig.add_axes([0, 0, 1, 1])
            ax.plot(np.linspace(-shift_y, shift_y - 1, num=shift_y * 2 - 1), err_y)
            fig.savefig("error_y.jpg", bbox_inches="tight")

    def col_shift(self, plot: bool = False) -> object:
        for i in range(int(len(self.proc) / 2)):
            # subtract corresponding image slices for reference
            subtraction = self.proc[i] - self.proc[-i - 1]

            err_baseline = np.sqrt(np.sum(np.square(subtraction)))

            shift_x = math.trunc(self.img.shape[2] / 10)

            err_x_left = np.empty((shift_x), dtype=np.float64)
            err_x_right = np.empty((shift_x), dtype=np.float64)

            err_x_left[0] = err_baseline
            err_x_right[0] = err_baseline

            # x-axis shift-right
            for c in range(1, shift_x):
                # subtract pixel values from first and last slices
                sub = self.proc[i][:, c:] - self.proc[-i - 1][:, :-c]
                err_x_right[c] = np.sqrt(np.sum(np.square(sub)))

            # x-axis shift-left
            for c in range(1, shift_x):
                # subtract pixel values from first and last slices
                sub = self.proc[i][:, :-c] - self.proc[-i - 1][:, c:]
                err_x_left[c] = np.sqrt(np.sum(np.square(sub)))

            vertex_right = np.amin(err_x_right)
            vertex_left = np.amin(err_x_left)

            if vertex_right < vertex_left:
                err_factor_x = np.where(err_x_right == vertex_right)[0][0]
                # correction_x = img[i][:, err_factor_x:] - img[-i-1][:, :-err_factor_x]
                self.proc[i] = self.proc[i][:, err_factor_x:]
                self.proc[-i - 1] = self.proc[-i - 1][:, :-err_factor_x]
                print(f"Shift right by {err_factor_x} columns")
            else:
                err_factor_x = np.where(err_x_left == vertex_left)[0][0]
                # correction_x = img[i][:, :-err_factor_x] - img[-i-1][:, err_factor_x:]
                self.proc[i] = self.proc[i][:, :-err_factor_x]
                self.proc[-i - 1] = self.proc[-i - 1][:, err_factor_x:]
                print(f"Shift right by {err_factor_x} columns")

        if plot:
            err_x = np.append(np.flip(err_x_right), err_x_left[1:])

            fig = plt.figure()
            ax = fig.add_axes([0, 0, 1, 1])
            ax.plot(np.linspace(-shift_x, shift_x - 1, num=shift_x * 2 - 1), err_x)
            fig.savefig("error_x.jpg", bbox_inches="tight")

    def crop(self):
        shape = list(self.proc[0].shape)

        for i in self.proc:
            if i.shape[0] < shape[0]:
                shape[0] = i.shape[0]
            if i.shape[1] < shape[1]:
                shape[1] = i.shape[1]

        for i in range(len(self.proc)):
            if self.proc[i].shape[0] > shape[0]:
                diff = self.proc[i].shape[0] - shape[0]

                if diff % 2:
                    self.proc[i] = self.proc[i][int(diff / 2) + 1 : int(-diff / 2)]
                else:
                    self.proc[i] = self.proc[i][int(diff / 2) : int(-diff / 2)]

            if self.proc[i].shape[1] > shape[1]:
                diff = self.proc[i].shape[1] - shape[1]

                if diff % 2:
                    self.proc[i] = self.proc[i][:, int(diff / 2) + 1 : int(-diff / 2)]
                else:
                    self.proc[i] = self.proc[i][:, int(diff / 2) : int(-diff / 2)]

        self.crop_stack = np.stack(self.proc, axis=0)

    def full_correction(self):
        self.row_shift()
        self.col_shift()
        self.crop()

    def calculate_col_filter(self) -> object:
        col_filter_vals = np.empty(
            (self.img.shape[0], self.img.shape[2]), dtype=np.float64
        )

        for i in range(self.img.shape[0]):
            col_filter_vals[i] = np.average(self.img[i], axis=0)

        return col_filter_vals

    def apply_col_filter(self, col_filter_vals: object):
        for plane in range(self.img.shape[0]):
            for row in range(self.img.shape[1]):
                self.img[plane][row] = self.img[plane][row] / col_filter_vals[plane]

    def save(self, fname: str):
        if self.crop_stack is not None:
            tf.imwrite(fname, self.crop_stack.astype(np.uint16), imagej=True)

    def show(self):
        viewer = napari.Viewer()

        viewer.dims.axis_labels = ("z", "y", "x")
        viewer.add_image(self.img, name="raw", visible=False)
        viewer.add_image(self.crop_stack, name="processed")

        napari.run()
