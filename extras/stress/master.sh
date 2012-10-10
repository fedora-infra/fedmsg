#!/bin/bash

# scp the 'mass-sub' script to worker nodes before running this.
# When you run this, wait until all the worker nodes stop counting their file
# descriptors and report "ready to receive"

# The max number of ssh connections to launch in parallel
N=50

# Do it.
(
    echo host1;
    echo host2;
    echo host3;
) | xargs -rP$N -L1 ./launcher.sh
