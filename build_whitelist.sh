#!/bin/bash

source /home/ivo/.virtualenvs/android-whitelist/bin/activate

export PYTHONPATH=.

python build_whitelist.py $@