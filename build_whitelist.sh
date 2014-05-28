#!/bin/bash

source /home/ivo/.virtualenvs/android-whitelist/bin/activate

export PYTHONPATH=.

python androidwhitelist/build_whitelist.py $@