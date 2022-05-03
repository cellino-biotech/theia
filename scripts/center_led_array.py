# ===============================================================================
#    Use XY encoder output signals to drive camera acquisition during scan
# ===============================================================================

import numpy as np

from basler.baslerace import ACA2040
from adafruit.matrixportal import MatrixPortal


# initialize devices
cam = ACA2040(exposure_time_us=30)
cam.set_trigger(source="Software")

mp = MatrixPortal()

img_seq_ver = cam.acquire_sequence(mp.height)
counter = 0
while counter < mp.height:
    msg = mp.read()
    if bool(msg):
        cam.dev.TriggerSoftware.Execute()

img_seq_hor = cam.acquire_sequence(mp.width)
counter = 0
while counter < mp.width:
    msg = mp.read()
    if bool(msg):
        cam.dev.TriggerSoftware.Execute()

cam.close()

avg_ver_arr = np.empty((mp.width), np.float64)
avg_hor_arr = np.empty((mp.width), np.float64)

for i in range(img_seq_ver.shape[0]):
    avg_ver_arr[i] = np.mean(img_seq_ver[i])

avg_ver_ind = 0
for i in range(1, avg_ver_arr.shape[0]):
    if avg_ver_arr[i] > avg_ver_arr[avg_ver_ind]:
        avg_ver_ind = i

print(f"Center column: {avg_ver_ind}")

for i in range(img_seq_hor.shape[0]):
    avg_hor_arr[i] = np.mean(img_seq_hor[i])

avg_hor_ind = 0
for i in range(1, avg_hor_arr.shape[0]):
    if avg_hor_arr[i] > avg_hor_arr[avg_hor_ind]:
        avg_hor_ind = i

print(f"Center row: {avg_hor_ind}")
