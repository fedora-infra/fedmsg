#!/usr/bin/env python
""" Subscribe to the public gateway N times.

It echoes a command to watch a count of file descriptors.  Run it.  When its
maxxed out, that's when its time to echo a message remotely.

"""

import sys
import os
import time
import zmq
import threading


# this is dumb!
N = 63
nailed = []

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
        #print '   Topic: %s, msg:%s' % (topic, msg)

        nailed.append(1)
        print len(nailed), "so far at", time.time() - start
        sys.stdout.flush()

print "watch \"ls -l /proc/%i/fd/ | wc -l\"" % os.getpid()

threads = [ThreadedJob() for i in range(N)]
for thread in threads:
    thread.start()

print "watch the fuck out"
for thread in threads:
    print "joining..", len(nailed), "so far."
    thread.join()

print "done with",  len(nailed)
