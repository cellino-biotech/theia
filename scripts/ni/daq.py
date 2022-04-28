import numpy as np
import matplotlib.pyplot as plt

from nidaqmx import Task
from nidaqmx.stream_readers import CounterReader
from nidaqmx.constants import AcquisitionType, CountDirection, Edge


class DAQ:
    def __init__(self, total_ticks: int):
        self.total_ticks = total_ticks

        self.ci_task = Task()

        self.channel = self.ci_task.ci_channels.add_ci_count_edges_chan(
            "Dev1/ctr0",
            initial_count=0,
            edge=Edge.FALLING,
            count_direction=CountDirection.COUNT_UP,
        )

        self.channel.ci_count_edges_term = "PFI0"

        self.ci_task.timing.cfg_samp_clk_timing(
            rate=50000,
            source="PFI1",
            active_edge=Edge.RISING,
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=self.total_ticks,
        )

        self.ci_task.in_stream.input_buf_size = self.total_ticks

        self.reader = CounterReader(self.ci_task.in_stream)
        self.reader.read_all_avail_samp = True

        self.count_arr = np.zeros(total_ticks, dtype=np.uint32)

    def start(self):
        self.ci_task.start()

        self.reader.read_many_sample_uint32(
            self.count_arr, number_of_samples_per_channel=self.total_ticks, timeout=0.1
        )

    def stop(self):
        self.ci_task.stop()
        self.ci_task.close()

    def plot_data(self):
        fig, (ax1, ax2) = plt.subplots(1, 2)
        fig.suptitle("DAQ signal recording")
        ax1.plot(self.count_arr)
        ax1.grid()

        deltas = self.count_arr[1:] - self.count_arr[:-1]
        ax2.plot([0, self.total_ticks], [0, self.total_ticks], "r--")
        ax2.plot(deltas, "k", alpha=0.5)
        ax2.plot(self.count_arr)
        ax2.grid()

        ax2.title("Skipped frames")
        ax2.xlabel("Encoder ticks")
        ax2.ylabel("Images captured")

        fig.show()
