# ===============================================================================
#    Flash entire LED array
# ===============================================================================

import time
import board
import displayio
import rgbmatrix
import framebufferio


DELAY = 2  # seconds

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
palette[1] = 0xD22B2B

# create Bitmap, TileGrid, and Group container objects
bitmaps = [displayio.Bitmap(display.width, display.height, 2) for _ in range(2)]
grids = [displayio.TileGrid(bitmaps[i], pixel_shader=palette) for i in range(2)]
groups = [displayio.Group() for _ in range(2)]

# add TileGrids to Group objects
for i in range(2):
    groups[i].append(grids[i])

for x in range(display.width):
    for y in range(display.height):
        bitmaps[0][x, y] = 1

for x in range(display.width):
    for y in range(display.height):
        bitmaps[1][x, y] = 0

while True:
    display.show(groups[0])
    time.sleep(DELAY)

    display.show(groups[1])
    time.sleep(DELAY)
