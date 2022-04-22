import nidaqmx
from nidaqmx.constants import (AcquisitionType, CountDirection, Edge, READ_ALL_AVAILABLE, TaskMode, TriggerType)
from nidaqmx.stream_readers import CounterReader
import time

"""
with nidaqmx.Task() as di_task:
    di_task.di_channels.add_di_chan('Dev1/port0/line0')
    g = di_task.read(number_of_samples_per_channel=10)
    print(g)
"""

with nidaqmx.Task() as ci_task:
    #channel = ci_task.ci_channels.add_ci_count_edges_chan('Dev1/ctr0',
    #    initial_count=0, edge=Edge.FALLING, count_direction=CountDirection.COUNT_UP)
    #channel = ci_task.ci_channels.add_ci_pulse_chan_ticks('Dev1/ctr0',
    #    source_terminal='PFI0')
    #channel.ci_period_term = '/Dev1/20MHzTimebase'

    #channel = ci_task.ci_channels.add_ci_pulse_chan_ticks()
    
    channel = ci_task.ci_channels.add_ci_count_edges_chan('Dev1/ctr0',
        initial_count=0, edge=Edge.FALLING, count_direction=CountDirection.COUNT_UP)
    channel.ci_count_edges_term = '/Dev1/20MHzTimebase'# 'PFI0'

    ci_task.timing.cfg_samp_clk_timing(rate=100000, source='PFI1', active_edge=Edge.FALLING,
        sample_mode=AcquisitionType.FINITE, samps_per_chan=10)


    ci_task.start()
    last = 0
    for n in range(5):
        ct = ci_task.read()
        print(ct-last, ct)
        last = ct
        time.sleep(0.5)