# ===============================================================================
#    Send serial commands to ASI stage.
# ===============================================================================

import time
import serial

from serial.tools import list_ports


def find_port(descriptor):
    ports = list(list_ports.comports())
    for com in ports:
        if descriptor in com.description:
            return com[0]

def connect(port, baudrate):
    controller = serial.Serial(port=port, baudrate=baudrate, \
        parity=serial.PARITY_NONE, bytesize=8, stopbits=1, \
            xonxoff=0, rtscts=0, timeout=1)
    return controller

def transmit(controller, command):
    command = command + '\r'
    controller.write(command.encode()) # pass as bytearray
    time.sleep(1)
    return controller.readline()[0:-1].decode("utf-8", "ignore")


if __name__ == "__main__":
    port = find_port("COM3")
    controller = connect(port, 9600)

    print(
        "Welcome to the ASI serial command program. Common commands include 'MOVE X=? Y=?'"
        "and 'WHERE X Y'. When finished, press 'q' to quit."
    )

    while True:
        cmd = input("--> ")

        if cmd == "q": break

        print("<--", transmit(controller, cmd))
    controller.close()
