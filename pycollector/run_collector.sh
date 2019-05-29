#!/usr/bin/env bash

source "./venv/bin/activate"
nohup python -u parsingthread.py > nohuplog.txt &

