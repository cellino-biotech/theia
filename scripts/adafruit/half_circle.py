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
bitmap0 = displayio.Bitmap(display.width, display.height, 2)
bitmap1 = displayio.Bitmap(display.width, display.height, 2)
bitmap2 = displayio.Bitmap(display.width, display.height, 2)
bitmap3 = displayio.Bitmap(display.width, display.height, 2)

# create corresponding Palette with two colors
palette = displayio.Palette(2)
palette[0] = 0x000000
palette[1] = 0xFFFFFF

# create TileGrid using the Bitmap and Palette
tile_grid0 = displayio.TileGrid(bitmap0, pixel_shader=palette)
tile_grid1 = displayio.TileGrid(bitmap1, pixel_shader=palette)
tile_grid2 = displayio.TileGrid(bitmap2, pixel_shader=palette)
tile_grid3 = displayio.TileGrid(bitmap3, pixel_shader=palette)

# create Group
group0 = displayio.Group()
group1 = displayio.Group()
group2 = displayio.Group()
group3 = displayio.Group()

# add TileGrid to Group
group0.append(tile_grid0)
group1.append(tile_grid1)
group2.append(tile_grid2)
group3.append(tile_grid3)

center = (20, 20)
radius = 8

# set bitmap0
for x in range(center[0], display.width):
    for y in range(display.height):
        # point lies inside circle if (x - center_x)² + (y - center_y)² < radius²
        if ((x - center[0]) ** 2 + (y - center[1]) ** 2) < (radius**2) or (
            (x - center[0]) ** 2 + (y - center[1]) ** 2
        ) == (radius**2):
            bitmap0[x, y] = 1
        else:
            bitmap0[x, y] = 0

for x in range(display.width):
    for y in range(center[1], display.height):
        # point lies inside circle if (x - center_x)² + (y - center_y)² < radius²
        if ((x - center[0]) ** 2 + (y - center[1]) ** 2) < (radius**2) or (
            (x - center[0]) ** 2 + (y - center[1]) ** 2
        ) == (radius**2):
            bitmap1[x, y] = 1
        else:
            bitmap1[x, y] = 0

for x in range(center[0]):
    for y in range(display.height):
        # point lies inside circle if (x - center_x)² + (y - center_y)² < radius²
        if ((x - center[0]) ** 2 + (y - center[1]) ** 2) < (radius**2) or (
            (x - center[0]) ** 2 + (y - center[1]) ** 2
        ) == (radius**2):
            bitmap2[x, y] = 1
        else:
            bitmap2[x, y] = 0

for x in range(display.width):
    for y in range(center[1]):
        # point lies inside circle if (x - center_x)² + (y - center_y)² < radius²
        if ((x - center[0]) ** 2 + (y - center[1]) ** 2) < (radius**2) or (
            (x - center[0]) ** 2 + (y - center[1]) ** 2
        ) == (radius**2):
            bitmap3[x, y] = 1
        else:
            bitmap3[x, y] = 0

delay = 1

while True:
    display.show(group0)
    time.sleep(delay)
    display.show(group1)
    time.sleep(delay)
    display.show(group2)
    time.sleep(delay)
    display.show(group3)
    time.sleep(delay)
