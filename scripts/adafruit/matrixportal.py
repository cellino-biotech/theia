import serial

from serial import SerialException
from serial.tools import list_ports


class SerialPort:
    """Managing RS232 serial connection"""

    def __init__(self, port: str, baudrate: int):
        # configure serial connection
        self.serial_port = serial.Serial()
        self.serial_port.port = port
        self.serial_port.baudrate = baudrate
        self.serial_port.parity = serial.PARITY_NONE
        self.serial_port.stopbits = serial.STOPBITS_ONE
        self.serial_port.xonxoff = False
        self.serial_port.rtscts = False
        self.serial_port.dsrdtr = False
        self.serial_port.timeout = 1

        # set size of rx/tx buffers before opening serial port
        self.serial_port.set_buffer_size(rx_size=12800, tx_size=12800)

        # open serial port
        try:
            self.serial_port.open()
        except SerialException:
            raise

        if self.serial_port.is_open:
            # clear buffers
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            print("MS-2000 connection successful")

    @staticmethod
    def find_port(descriptor):
        ports = list(list_ports.comports())
        for com in ports:
            if descriptor in com.description:
                return com[0]

    def send(self, cmd: str):
        # good practice to reset buffers before each transmission
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()

        cmd = cmd + "\r"
        self.serial_port.write(cmd.encode())  # pass as bytearray

    def read(self) -> str:
        return self.serial_port.readline().decode("utf-8", "ignore").strip()

    def close(self):
        if self.serial_port.is_open:
            self.serial_port.close()


class MatrixPortal(SerialPort):
    # valid baudrates
    BAUDRATES = [9600, 19200, 28800, 115200]

    def __init__(self, port: str, baudrate: int = 115200):
        super().__init__(port, baudrate)

        # validate user baudrate
        if baudrate not in self.BAUDRATES:
            raise ValueError(
                "Invalid baudrate. Valid rates include 9600, 19200, 28800, 115200"
            )

        self.height = 64
        self.width = 64
