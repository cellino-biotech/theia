import nidaqmx


def illuminator(on_state: bool = True):
    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan("Dev1/port0/line0")
        task.write(on_state)


if __name__ == "__main__":
    illuminator()
