import time
import board
import terminalio
from adafruit_matrixportal.matrixportal import MatrixPortal
import displayio
import rgbmatrix
import framebufferio

#matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)

displayio.release_displays()
matrix = rgbmatrix.RGBMatrix(
    width=64, height=64, bit_depth=4,
    rgb_pins=[
        board.MTX_R1,
        board.MTX_G1,
        board.MTX_B1,
        board.MTX_R2,
        board.MTX_G2,
        board.MTX_B2
    ],
    addr_pins=[
        board.MTX_ADDRA,
        board.MTX_ADDRB,
        board.MTX_ADDRC,
        board.MTX_ADDRD,
        board.MTX_ADDRE
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE
)
display = framebufferio.FramebufferDisplay(matrix)

# Create a bitmap with two colors
bitmap = displayio.Bitmap(display.width, display.height, 2)
bitmap1 = displayio.Bitmap(display.width, display.height, 2)

# Create a two color palette
palette = displayio.Palette(2)
palette[0] = 0x000000
palette[1] = 0xFF0000

# Create a TileGrid using the Bitmap and Palette
tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
tile_grid1 = displayio.TileGrid(bitmap1, pixel_shader=palette)

# Create a Group
group = displayio.Group()
group1 = displayio.Group()

# Add the TileGrid to the Group
group.append(tile_grid)
group1.append(tile_grid1)


for x in range(64):
    for y in range(64):
        bitmap[x,y] = 1 if x > 31 else 0
        bitmap1[x,y] = 1 if x < 32 else 0

# Add the Group to the Display
while True:
    display.show(group)
    time.sleep(0.25)
    display.show(group1)
    time.sleep(0.25)

#make half the board light up
if False:
    cond = 0
    while True:
        for x in range(64):
            for y in range(64):
                if cond == 0:
                    bitmap[x,y] = 1 if x > 31 else 0
                elif cond == 1:
                    bitmap[x,y] = 1 if y > 31 else 0
                elif cond == 2:
                    bitmap[x,y] = 1 if x < 32 else 0
                else:
                    bitmap[x,y] = 1 if y < 32 else 0
        cond = cond + 1
        if cond > 3:
            cond = 0

while True:
    pass
