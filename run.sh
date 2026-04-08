#!/bin/bash
# VRMS Launch Script
export DISPLAY=:0

cd /opt/vrms1
source venv/bin/activate

python3 main.py
