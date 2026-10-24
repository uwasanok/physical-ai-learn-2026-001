#!/bin/bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
set -u
mkdir -p output logs
Xvfb :99 -screen 0 1280x800x24 -ac >logs/xvfb.log 2>&1 &
sleep 1
openbox >logs/openbox.log 2>&1 &
x11vnc -display :99 -forever -shared -nopw -localhost >logs/vnc.log 2>&1 &
websockify --web=/usr/share/novnc 6080 localhost:5900 >logs/websockify.log 2>&1 &
exec python3 -m notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root --notebook-dir=/work
