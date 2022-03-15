import json
import pathlib

from pycromanager import Bridge, Acquisition

# directories
ROOT_DIR = pathlib.Path(__file__).parent.parent
SAVE_PATH = ROOT_DIR / "images"

# generate list of event dicts (+/- 40um from z-pos)
events = []
for i in range(-40, 40, 2):
    events.append(
        {
            # TODO: learn more about channel groups
            "channel": {
              "group": "zstack",
              "config": "8-bit_F-focus"
            },
            # "x": 2.34855 * 1000,
            # "y": 7.10405 * 1000,
            "z": i,
            "keep_shutter_open": True # keep shutter open during image acquisition
        }
    )

with Bridge() as bridge:
    # create a micro-manager core object
    core = bridge.get_core()

    acq = Acquisition(
        directory=SAVE_PATH,
        name="zstack"
    )

    acq.acquire(events)
