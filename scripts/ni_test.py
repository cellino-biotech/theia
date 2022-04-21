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
    channel = ci_task.ci_channels.add_ci_count_edges_chan('Dev1/ctr0',
        initial_count=0, edge=Edge.FALLING, count_direction=CountDirection.COUNT_UP)
    channel.ci_count_edges_term = 'PFI0' #'/Dev1/20MHzTimebase'
    
    # TODO: attempt to get gated counts... somehow not working
    #channel.ci_count_edges_gate_term = '/Dev1/PFI9'
    #channel.ci_count_edges_gate_enable = True

    #ci_task.ci_channels.add_ci_count_edges_chan('Dev1/ctr0')
    ci_task.start()
    last = 0
    for n in range(30):
        ct = ci_task.read()
        print(ct-last, ct)
        last = ct
        time.sleep(0.5)