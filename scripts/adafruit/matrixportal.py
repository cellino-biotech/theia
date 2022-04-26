import serial

from serial import SerialException


class MatrixPortal:
    def __init__(self, port: str = "COM3", baudrate: int = 115200):
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

        # open serial port
        try:
            self.serial_port.open()
        except SerialException:
            raise

        if self.serial_port.is_open:
            # clear buffers
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            print("MatrixPortal connection successful")

    def read(self) -> str:
        response = self.serial_port.readline().decode("utf-8", "ignore").strip()

        return response
