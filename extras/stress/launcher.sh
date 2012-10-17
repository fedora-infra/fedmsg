#!/bin/bash

# Just an intermediary script to make invocation from xargs easier.

echo "SSHing to $1"
ssh -tt $1 "bash -c 'source ~/fedmsg/bin/activate; (echo 1;echo 2;echo 3;echo 4;echo 5;echo 6;echo 7) | xargs -rP8 -L1 ./mass-sub.py'"
