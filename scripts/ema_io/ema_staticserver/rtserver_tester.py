__author__ = 'Kristy'

"""
This module encapsulates a very simple test of the rtserver, in whichever form it is running.
Acting as a client, it makes several calls to the rtserver that do not involve threading.
Output is printed to stderr.
"""


from scripts.ema_io.client_server_comms import ClientConnection
import scripts.ema_shared.properties as pps
import time

# from RT Client
conn = ClientConnection((pps.waveserver_host, pps.waveserver_port))

messages = [
    ("sendparameters", 1),
    ("sendcurrentframe 3d", 1),
    ("sendcurrentframe", 1),
    ("streamframes frequency:30 3d", 1),
    ("streamframes stop", 1),
]

for m, mt in messages:
    conn.send_rcv_packet(m, msgtype=mt, )
    time.sleep(1)