# ===============================================================================
#    Display semicircle at arbitrary angles based on a division number
# ===============================================================================

import board
import displayio
import rgbmatrix
import framebufferio


CENTER = (31.5, 31.5)  # pixel coordinates
RADIUS = 11  # pixels
THICKNESS = 3  # pixels


points = []


def point_inside_circle(x: int, y: int, r: int) -> bool:
    """Determine if point (x, y) is inside circle or on perimeter"""

    # point lies inside circle if (x - center_x)² + (y - center_y)² < radius²
    return ((x - CENTER[0]) ** 2 + (y - CENTER[1]) ** 2) < (r**2) or (
        (x - CENTER[0]) ** 2 + (y - CENTER[1]) ** 2
    ) == (r**2)


for x in range(64):
    for y in range(64):
        # point lies inside circle if (x - center_x)² + (y - center_y)² < radius²
        if point_inside_circle(x, y, RADIUS) and not point_inside_circle(
            x, y, RADIUS - THICKNESS
        ):
            points.append([x, y])

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
palette[1] = 0xFF0000

# create Bitmap, TileGrid, and Group container objects
bitmap = displayio.Bitmap(display.width, display.height, 2)
grid = displayio.TileGrid(bitmap, pixel_shader=palette)
group = displayio.Group()

# add TileGrid to Group object
group.append(grid)

# assign pixel map to Group
for p in points:
    bitmap[p[0], p[1]] = 1

display.show(group)

while True:
    pass
