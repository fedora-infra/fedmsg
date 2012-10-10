#!/bin/bash

# Just an intermediary script to make invocation from xargs easier.

echo "SSHing to $1"
ssh -tt $1 "source ~/.virtualenvs/fedmsg/bin/activate; ./mass-sub.py"
