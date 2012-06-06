""" Test config. """
import socket
hostname = socket.gethostname()

config = dict(
    endpoints={
        "unittest.%s" % hostname: ["tcp://*:98765"],
        "twisted.%s" % hostname: ["tcp://*:98764"],
    },
    relay_inbound="tcp://127.0.0.1:2003",
    environment="dev",
    high_water_mark=0,
    io_threads=1,
    irc=[],
    zmq_enabled=True,
    zmq_strict=False,
)
