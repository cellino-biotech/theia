import tie
import copy
import json
import numpy as np
import pycromanager as pm

from pycromanager import Acquisition


counter = 0

planes_per_z_stack = 3
lambd = 6.328e-07  # wavelength of the illumination light (meters)
debug = True  # compute the phase image form test data in previous cell

def img_process_fn(image, metadata):
    """
    runs each time an image is acquired
    if the image is the last in the z-stack, the inverse problem will be solved, 
    and the result added to the GUI; otherwise image will be accumulated into a temporary list
    """

    global counter

    # accumulate images as they come
    if not hasattr(img_process_fn, "images"):
        img_process_fn.images = []
        img_process_fn.z_positions = []

    # add pixels and z position
    img_process_fn.images.append(image)
    img_process_fn.z_positions.append(metadata["ZPosition_um_Intended"])

    if metadata["Axes"]["z"] == planes_per_z_stack - 1:
        # its the final one in the z stack

        z_positions = np.array(img_process_fn.z_positions)
        images = np.stack(img_process_fn.images, axis=2).astype(float)

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

        with open(f'C:/Users/lukas/Desktop/metadata{counter}.json', 'w') as f:
            json.dump(metadata, f)

        # return the original image and the phase image, in a new channel
        return [(image, metadata), (phase_img, phase_image_metadata)]
    else:
        with open(f'C:/Users/lukas/Desktop/metadata{counter}.json', 'w') as f:
            json.dump(metadata, f)
            counter += 1
        return image, metadata

img_process_fn.images = []
img_process_fn.z_positions = []

with Acquisition(
    directory="C:/Users/lukas/Desktop", name="acq_name", image_process_fn=img_process_fn
) as acq:
    # Generate the events for a single z-stack
    events = pm.multi_d_acquisition_events(z_start=0, z_end=10, z_step=5)
    acq.acquire(events)