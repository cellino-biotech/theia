import time
import board
import displayio
import rgbmatrix
import terminalio
import framebufferio


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

# create Bitmap with two colors
bitmap0 = displayio.Bitmap(display.width, display.height, 2)
bitmap1 = displayio.Bitmap(display.width, display.height, 2)

# create corresponding Palette with two colors
palette = displayio.Palette(2)
palette[0] = 0x000000
palette[1] = 0xFFF

# create TileGrid using the Bitmap and Palette
tile_grid0 = displayio.TileGrid(bitmap0, pixel_shader=palette)
tile_grid1 = displayio.TileGrid(bitmap1, pixel_shader=palette)

# create Group
group0 = displayio.Group()
group1 = displayio.Group()

# add TileGrid to Group
group0.append(tile_grid0)
group1.append(tile_grid1)

for x in range(display.width):
    for y in range(display.height):
        bitmap0[x, y] = 1 if x > 31 else 0
        bitmap1[x, y] = 1 if x < 32 else 0

# add Group to Display
while True:
    print("show display")
    display.show(group0)
    time.sleep(0.25)
    display.show(group1)
    time.sleep(0.25)
