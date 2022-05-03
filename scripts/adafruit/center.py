import time
import board
import displayio
import rgbmatrix
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
bitmap = displayio.Bitmap(display.width, display.height, 2)

# create corresponding Palette with two colors
palette = displayio.Palette(2)
palette[0] = 0x000000
palette[1] = 0xFFFFFF

# create TileGrid using the Bitmap and Palette
tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)

# create Group
group = displayio.Group()

# add TileGrid to Group
group.append(tile_grid)

timeout = 0.01

while True:
    for col in range(display.width):
        for x in range(display.width):
            for y in range(display.height):
                bitmap[x, y] = 1 if x == col else 0
        display.show(group)
        time.sleep(timeout)
        print("1")
        time.sleep(timeout)

    for y in range(display.height):
        bitmap[display.width - 1, y] = 0
    display.show(group)

    for row in range(display.height):
        for y in range(display.height):
            for x in range(display.width):
                bitmap[x, y] = 1 if y == row else 0
        display.show(group)
        time.sleep(timeout)
        print("1")
        time.sleep(timeout)

    for x in range(display.width):
        bitmap[x, display.height - 1] = 0
    display.show(group)
