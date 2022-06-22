# ===============================================================================
#    Display semicircle at right angles (0, 90, 180, 270 deg)
# ===============================================================================

import time
import math
import board
import displayio
import rgbmatrix
import framebufferio


CENTER = (31.5, 31.5)  # pixel coordinates
RADIUS = 7  # pixels
DELAY = 3  # seconds


def point_inside_circle(x: int, y: int) -> bool:
    """Determine if point (x, y) is inside circle or on perimeter"""

    # point lies inside circle if (x - center_x)² + (y - center_y)² < radius²
    return ((x - CENTER[0]) ** 2 + (y - CENTER[1]) ** 2) < (RADIUS**2) or (
        (x - CENTER[0]) ** 2 + (y - CENTER[1]) ** 2
    ) == (RADIUS**2)


# free up display buses and pins
displayio.release_displays()

# parallel bus configuration
matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=64,
    bit_depth=4,
    rgb_pins=[
        board.MTX_R1,
        board.MTX_G1,
        board.MTX_B1,
        board.MTX_R2,
        board.MTX_G2,
        board.MTX_B2,
    ],
    addr_pins=[
        board.MTX_ADDRA,
        board.MTX_ADDRB,
        board.MTX_ADDRC,
        board.MTX_ADDRD,
        board.MTX_ADDRE,
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE,
)

display = framebufferio.FramebufferDisplay(matrix)

# create Palette with two colors
palette = displayio.Palette(2)
palette[0] = 0x000000
palette[1] = 0xFFFFFF

# create Bitmap, TileGrid, and Group container objects
bitmaps = [displayio.Bitmap(display.width, display.height, 2) for _ in range(4)]
grids = [displayio.TileGrid(bitmaps[i], pixel_shader=palette) for i in range(4)]
groups = [displayio.Group() for _ in range(4)]

for i in range(4):
    groups[i].append(grids[i])

# set bitmaps
for x in range(math.ceil(CENTER[0]), display.width):
    for y in range(display.height):
        if point_inside_circle(x, y):
            bitmaps[0][x, y] = 1
        else:
            bitmaps[0][x, y] = 0

for x in range(display.width):
    for y in range(math.ceil(CENTER[1]), display.height):
        if point_inside_circle(x, y):
            bitmaps[1][x, y] = 1
        else:
            bitmaps[1][x, y] = 0

for x in range(math.ceil(CENTER[0])):
    for y in range(display.height):
        if point_inside_circle(x, y):
            bitmaps[2][x, y] = 1
        else:
            bitmaps[2][x, y] = 0

for x in range(display.width):
    for y in range(math.ceil(CENTER[1])):
        if point_inside_circle(x, y):
            bitmaps[3][x, y] = 1
        else:
            bitmaps[3][x, y] = 0

while True:
    for i in range(len(groups)):
        display.show(groups[i])
        time.sleep(DELAY)
