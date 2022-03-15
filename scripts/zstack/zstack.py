import json
import pathlib

from pycromanager import Bridge, Acquisition

# directories
ROOT_DIR = pathlib.Path(__file__).parent.parent
ZPOS_PATH = ROOT_DIR / "settings" / "zpos.json"
SAVE_PATH = ROOT_DIR / "images"

# store z-pos in external file
zpos = json.load(open(ZPOS_PATH))
zpos_ibidi = zpos["ibidi_slide"]

# generate list of event dicts (+/- 40um from z-pos)
events = []
for i in range(-40, 40, 2):
    events.append(
        {
            # "x": 2.34855 * 1000,
            # "y": 7.10405 * 1000,
            "z": (zpos_ibidi + i/1000) * 1000,
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
