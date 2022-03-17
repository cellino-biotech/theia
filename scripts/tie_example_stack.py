import os
import copy
import json
import numpy as np
import tie_modified as tie

from PIL import Image, ImageSequence


planes_per_z_stack = 3  # number of images in stack
lambd = 6.328e-07       # wavelength of the illumination light (meters)

DATA_PATH = "C:/Users/lukas/Desktop/Data"

def img_process_fn(image, metadata):
    """
    runs each time an image is acquired
    if the image is the last in the z-stack, the inverse problem will be solved, 
    and the result added to the GUI; otherwise image will be accumulated into a temporary list
    """

    # accumulate images as they come
    if not hasattr(img_process_fn, "images"):
        img_process_fn.images = []
        img_process_fn.z_positions = []

    # add pixels and z position
    img_process_fn.images.append(image)
    img_process_fn.z_positions.append(metadata["ZPosition_um_Intended"])

    if metadata["Axes"]["z"] == planes_per_z_stack - 1:
        # its the final one in the z stack

        z_positions = np.array(img_process_fn.z_positions, dtype=np.float)
        z_positions *= 1e-6
        images = np.stack(img_process_fn.images, axis=2).astype(float)
        images = images/np.max(images)

        # the z position that is solved for -- assume this is the median of the z-stack (i.e. its symmetrical)
        solved_plane_index = np.argmin(np.abs(z_positions - np.median(z_positions)))

        phase_img = tie.GP_TIE(
            images,
            z_positions,
            lambd,
            1e-6 * metadata["PixelSizeUm"],
            solved_plane_index,
        )

        # rescale to 16 bit, since the viewer doesn't accept 32 bit floats
        phase_img = (
            ((phase_img - np.min(phase_img)) / (np.max(phase_img) - np.min(phase_img)))
            * (2 ** 16 - 1)
        ).astype(">u2")

        # create new metadta to go along with this phase image
        phase_image_metadata = copy.deepcopy(metadata)
        # make it appear as a new channel
        phase_image_metadata["Channel"] = "Phase"
        # Put it the z index closest to the solved plane
        phase_image_metadata["Axes"]["z"] = solved_plane_index

        # reset in case multiple z-stacks
        img_process_fn.images = []
        img_process_fn.z_positions = []

        # return the original image and the phase image, in a new channel
        img = Image.fromarray(phase_img)
        img.save(os.path.join(DATA_PATH, "phase_img.tif"))
        return [(image, metadata), (phase_img, phase_image_metadata)]
    else:
        return image, metadata


if __name__ == "__main__":
    # open multi-image tiff file
    # stack = Image.open(os.path.join(DATA_PATH, "stack.tif"))

    # for i, page in enumerate(ImageSequence.Iterator(stack)):
    #     metadata = json.load(open(os.path.join(DATA_PATH, f"metadata{i}.json")))
    #     img_process_fn(page, metadata)

    #     page.save(os.path.join(DATA_PATH, f"stack{i}.tif"))
    for i in range(planes_per_z_stack):
        img = Image.open(os.path.join(DATA_PATH, f"stack{i}.tif"))
        metadata = json.load(open(os.path.join(DATA_PATH, f"metadata{i}.json")))
        img_process_fn(img, metadata)