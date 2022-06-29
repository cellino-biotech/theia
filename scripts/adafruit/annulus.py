# ===============================================================================
#    Display semicircle at arbitrary angles based on a division number
# ===============================================================================

import time
import math
import board
import displayio
import rgbmatrix
import framebufferio


CENTER = (31.5, 31.5)  # pixel coordinates
RADIUS = 15  # pixels
THICKNESS = 3
DIV = 4  # DIV=8 corresponds to 0, 30, 60, 90 deg
DELAY = 2  # seconds


def boundary_points(theta: float) -> list:
    """Determine points that define circle diameter at some angle"""

    x = RADIUS * math.cos(theta)
    y = RADIUS * math.sin(theta)

    return [
        [math.ceil(CENTER[0] + x), math.ceil(CENTER[1] + y)],
        [math.floor(CENTER[0] - x), math.floor(CENTER[1] - y)],
    ]


def point_inside_circle(x: int, y: int, r: int) -> bool:
    """Determine if point (x, y) is inside circle or on perimeter"""

    # point lies inside circle if (x - center_x)² + (y - center_y)² < radius²
    return ((x - CENTER[0]) ** 2 + (y - CENTER[1]) ** 2) < (r**2) or (
        (x - CENTER[0]) ** 2 + (y - CENTER[1]) ** 2
    ) == (r**2)


step = 2 * math.pi / DIV
steps = [i * step for i in range(int(DIV / 2))]
points = [[] for _ in range(DIV)]

# calculate points for outer circle
for i in range(len(steps)):
    (a, b) = boundary_points(steps[i])

    for x in range(64):
        for y in range(64):
            # point lies inside circle if (x - center_x)² + (y - center_y)² < radius²
            if point_inside_circle(x, y, RADIUS) and not point_inside_circle(
                x, y, RADIUS - THICKNESS
            ):
                # only perform computation if point is eligible
                d = (x - a[0]) * (b[1] - a[1]) - (y - a[1]) * (b[0] - a[0])

                if d > 0:
                    points[i].append([x, y])
                elif d < 0:
                    points[i + int(DIV / 2)].append([x, y])
                else:
                    # if point lies on diameter line (which should not be possible if
                    # using floating point center coordinate), add to both lists
                    points[i].append([x, y])
                    points[i + int(DIV / 2)].append([x, y])

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
bitmaps = [displayio.Bitmap(display.width, display.height, 2) for _ in range(DIV)]
grids = [displayio.TileGrid(bitmaps[i], pixel_shader=palette) for i in range(DIV)]
groups = [displayio.Group() for _ in range(DIV)]

# add TileGrids to Group objects
for i in range(DIV):
    groups[i].append(grids[i])

# assign pixel maps to Groups
for j in range(DIV):
    for p in points[j]:
        bitmaps[j][p[0], p[1]] = 1

while True:
    for k in range(DIV):
        display.show(groups[k])
        time.sleep(DELAY)
