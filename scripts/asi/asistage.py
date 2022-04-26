# ===============================================================================
#    Serial setup for ASI stage
# ===============================================================================

import serial

from serial import SerialException


class SerialPort:
    """Managing RS232 serial connection"""

    def __init__(self, port: str, baudrate: int, report: bool = True):
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
        self.report = report

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
        ports = list(serial.tools.list_ports.comports())
        for com in ports:
            if descriptor in com.description:
                return com[0]

    def send_command(self, command: str):
        # good practice to reset buffers before each transmission
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()

        command = command + "\r"
        self.serial_port.write(command.encode())  # pass as bytearray

    def read_response(self, print_to_console: bool = True) -> str:
        response = self.serial_port.readline().decode("utf-8", "ignore").strip()

        if print_to_console:
            # B == one or more motors running   N == no motors running
            if response != "B" and response != "N":
                print(f"<-- {response}")
        return response

    def close(self):
        if self.serial_port.is_open:
            self.serial_port.close()


class MS2000(SerialPort):
    """Serial connection to MS2000 controller

    Error codes:
        :N-1        Unknown command
        :N-2        Unrecognized axis parameter
        :N-3        Missing parameters (command requires one or more axis parameters)
        :N-4        Parameter out of range
        :N-5        Operation failed
        :N-6        Undefined error
        :N-7..20    Reserved for filterwheel
        :N-21       Serial command halted by the HALT command
        :N-30..39   Reserved
    """

    # valid baudrates
    BAUDRATES = [9600, 19200, 28800, 115200]

    def __init__(self, port: str, baudrate: int = 115200):
        super().__init__(port, baudrate)

        # validate user baudrate
        if baudrate not in self.BAUDRATES:
            raise ValueError(
                "Invalid baudrate. Valid rates include 9600, 19200, 28800, 115200"
            )

    def moverel(self, x: int = 0, y: int = 0, z: int = 0, f: int = 0):
        """Relative stage translation"""
        self.send_command(f"R X={x} Y={y} Z={z} F={f}")
        self.read_response()

    def moverel_axis(self, axis: str, dist: int):
        "Relative translation for specific axis"
        self.send_command(f"R {axis}={dist}")
        self.read_response()

    def move(self, x: int = 0, y: int = 0, z: int = 0, f: int = 0):
        "Absolute stage translation"
        self.send_command(f"M X={x} Y={y} Z={z} F={f}")
        self.read_response()

    def move_axis(self, axis: str, dist: int):
        "Absolute translation for specific axis"
        self.send_command(f"M {axis}={dist}")
        self.read_response()

    def set_speed(self, x: int = None, y: int = None, z: int = None):
        """Set motor velocity in mm/s"""
        if x and y and z:
            self.send_command(f"S X={x} Y={y} Z={z}")
        elif x and y:
            self.send_command(f"S X={x} Y={y}")
        elif x and z:
            self.send_command(f"S X={x} Z={z}")
        elif y and z:
            self.send_command(f"S Y={y} Z={z}")
        elif x:
            self.send_command(f"S X={x}")
        elif y:
            self.send_command(f"S Y={y}")
        elif z:
            self.send_command(f"S Z={z}")
        else:
            return
        self.read_response()

    def home_all(self):
        """Home all axes"""
        self.send_command("! X Y Z")
        self.read_response()

    def home_axis(self, axis: str):
        """Home specifc axis"""
        self.send_command(f"! {axis}")
        self.read_response()

    def load_buffer(self, x: int = 0, y: int = 0, z: int = 0):
        """Load ring buffer (max 50 positions)"""
        self.send_command(f"LD X={x} Y={y} Z={z}")
        self.read_response()

    def set_max_speed(self, axis: str, speed: int):
        "Set the speed (mm/s) for a specific axis"
        self.send_command(f"S {axis}={speed}")
        self.read_response()

    def scan_x_axis_enc(self, start: int, num_pix: int, enc_divide: int = 35):
        self.ttl(x=1)
        self.send_command(f"NR X={start} Z={enc_divide} F={num_pix}")
        self.read_response()
        self.send_command("SN X=1 Y=0 Z=0 F=0")
        self.read_response()
        self.send_command("SN")
        self.read_response()

    def scan_x_axis(self, start: int, stop: int):
        # set ttl to output at x constant move
        self.ttl(y=3)
        self.send_command(f"NR X={start} Y={stop}")
        self.read_response()
        self.send_command("SN X=1 Y=0 Z=0 F=0")
        self.read_response()
        self.send_command("SN")
        self.read_response()

    def scan_y_axis(self, start: int, stop: int):
        # set ttl to output at y constant move
        self.ttl(y=4)
        self.send_command(f"NR X={start} Y={stop}")
        self.read_response()
        self.send_command("SN X=0 Y=1 Z=0 F=0")
        self.read_response()
        self.send_command("SN")
        self.read_response()

    def set_ring_buffer(self, axis_byte: int = 15):
        """Configure ring buffer for individual axis control"""
        self.send_command(f"RM Y={axis_byte}")
        self.read_response()

    def ttl(self, x: int = 0, y: int = 0):
        self.send_command(f"TTL X={x} Y={y}")
        self.read_response()

    def get_position(self, axis: str) -> int:
        """Return position of the stage in ASI units (tenths of microns)"""
        self.send_command(f"WHERE {axis}")
        response = self.read_response()
        return int(response.split(" ")[1])

    def get_position_um(self, axis: str) -> float:
        """Return position of the stage in microns"""
        pos = self.get_position(axis)
        return pos / 10.0

    def set_origin(self):
        """Sets current position as origin point"""
        self.send_command("Z")
        self.read_response()

    def halt_all_motion(self):
        """Stop all active motors"""
        self.send_command("\\")
        self.read_response()

    def save_settings(self):
        """Save settings to flash memory"""
        self.send_command("SS Z")
        self.read_response()

    # ------------------------------ #
    #    MS2000 Utility Functions    #
    # ------------------------------ #

    def is_device_busy(self) -> bool:
        """Returns True if axis is busy"""
        self.send_command("/")
        if "B" in self.read_response():
            return True
        else:
            return False

    def wait_for_device(self, report: bool = False):
        """Wait for all motors to reach target positions"""
        if not report:
            print("Waiting for device...")
        temp = self.report
        self.report = report
        busy = True
        while busy:
            busy = self.is_device_busy()
        self.report = temp
