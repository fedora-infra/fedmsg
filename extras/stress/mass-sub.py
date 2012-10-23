#!/usr/bin/env python
""" Subscribe to the public gateway N times.

It echoes a command to watch a count of file descriptors.  Run it.  When its
maxxed out, that's when its time to echo a message remotely.

scp this to remote worker nodes and launch them all at the same time with
"./master.sh"

"""

import sys
import os
import time
import zmq
import socket
import threading


# this is dumb!
N = 63

prefix = '[' + socket.gethostname().center(15) + ']'

ctx = zmq.Context()

start = time.time()

class ThreadedJob(threading.Thread):
    def run(self):
        self.ctx = ctx
        self.s = self.ctx.socket(zmq.SUB)
        connect_to = "tcp://hub.fedoraproject.org:9940"
        self.s.connect(connect_to)
        self.s.setsockopt(zmq.SUBSCRIBE,'')
        topic, msg = self.s.recv_multipart()
        sys.stdout.flush()

threads = [ThreadedJob() for i in range(N)]
for thread in threads:
    thread.start()

pid = os.getpid()
print prefix, "Checking pid", pid
target = 200
length = 0
while length <= target:
    length = len(os.listdir("/proc/%i/fd/" % os.getpid()))
    print prefix, length, "is less than", target
    time.sleep(1)

print prefix, "ready to receive..."

for thread in threads:
    thread.join()

print prefix, "Done."
