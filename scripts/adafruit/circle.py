import time
import board
import displayio
import rgbmatrix
import framebufferio

from adafruit_display_shapes.circle import Circle


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

# set brightness to max value
# NOTE: any value between 0 and 1.0 does not produce a noticeable affect
display.brightness = 1.0

# set refresh rate
display.refresh(target_frames_per_second=60, minimum_frames_per_second=1)

# generate white circle with radius 15 pix at location (27, 34)
circle = Circle(27, 34, 10, fill=0xFFFFFF)

# create Group
group = displayio.Group()

# add Circle to Group
group.append(circle)

display.show(group)

while True:
    pass
