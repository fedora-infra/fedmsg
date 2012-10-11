config = {
    # This is the port for a special, outbound ZMQ pub socket on which we'll
    # rebroadcast everything on the fedmsg bus.
    'fedmsg.consumers.gateway.port': 9940,

    # Set this number to near, but not quite the fs.file-limit.  Try 160000.
    'fedmsg.consumers.gateway.high_water_mark': 10000,
}
