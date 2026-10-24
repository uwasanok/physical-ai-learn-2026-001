"""Launch only this project's processes, collect logs, and always clean them up."""
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
(ROOT/'logs').mkdir(exist_ok=True)
lock=(ROOT/'logs/run.lock').open('w')
try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError: raise SystemExit('A simulation is already running. Stop it before starting another.')
processes=[]; files=[]
def launch(command,log):
    stream=(ROOT/'logs'/log).open('w'); files.append(stream)
    process=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    processes.append(process); return process
try:
    subprocess.run([sys.executable,'scripts/make_world.py'],check=True)
    subprocess.run([sys.executable,'scripts/intent_model.py'],check=True)
    sim=launch(['gz','sim','-s','-r','world/step1.sdf'],'gazebo.log')
    bridge=launch(['ros2','run','ros_gz_bridge','parameter_bridge','--ros-args','-p','config_file:=/work/config/bridge.yaml'],'bridge.log')
    time.sleep(3)
    if sim.poll() is not None or bridge.poll() is not None: raise RuntimeError('Simulator or bridge exited. See logs.')
    controller=launch([sys.executable,'scripts/controller.py','--demo'],'controller.log')
    code=controller.wait(timeout=265)
    print((ROOT/'logs/controller.log').read_text(),flush=True)
    if code: raise SystemExit(code)
finally:
    for process in reversed(processes):
        if process.poll() is None:
            os.killpg(process.pid,signal.SIGINT)
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL); process.wait()
    for stream in files: stream.close()
