"""Validate end-to-end evidence; this does not replace course grading."""
import csv
import json
import math
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'output'
run=json.loads((OUT/'run_result.json').read_text())
ai=json.loads((OUT/'intent_evaluation.json').read_text())
rows=list(csv.DictReader((OUT/'trajectory.csv').open()))
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=width,height,codec_name','-of','json',str(OUT/'demo.mp4')]))
assert run['success'] and [g['intent'] for g in run['goals']]==['inspection','supply','home']
assert all(g['error_m']<0.10 for g in run['goals'])
assert ai['correct']==ai['test_examples'] and all(r['predicted']=='unknown' for r in ai['out_of_domain'])
assert 60<=float(probe['format']['duration'])<=180
assert len(rows)>100 and max(float(r['x']) for r in rows)>1.8 and max(float(r['y']) for r in rows)>1.6
stop_rows=[r for r in rows if r['intent'] in ('stop','unknown') and float(r['wall_seconds'])>50]
assert len(stop_rows)>10 and all(float(r['linear_velocity'])==0 and float(r['angular_velocity'])==0 for r in stop_rows)
drift=max(math.hypot(float(r['x'])-float(stop_rows[0]['x']),float(r['y'])-float(stop_rows[0]['y'])) for r in stop_rows)
assert drift<0.02
assert run['camera_messages']>300
result={'passed':True,'checks':['3 ordered waypoint arrivals within 0.10 m','8 authored holdout instructions classified correctly','3 selected unknown commands rejected','MP4 duration within 60-180 seconds','recorded trajectory moved across both axes','zero commanded velocity for stop/unknown after return','stationary drift below 0.02 m','Gazebo camera messages received'], 'stationary_drift_m':drift,'video':probe}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,indent=2))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(7,4.5))
ax.plot([float(r['x']) for r in rows],[float(r['y']) for r in rows],color='#1976a3',linewidth=2,label='ROS odometry')
for label,x,y in [('Home',0,0),('Inspection',2,0),('Supply',2,1.8)]:
    ax.scatter(x,y,s=65,zorder=4); ax.annotate(label,(x,y),xytext=(6,8),textcoords='offset points')
    ax.add_patch(plt.Circle((x,y),0.1,fill=False,color='gray',linestyle='--'))
ax.set(xlabel='x [m]',ylabel='y [m]',title='Actual Gazebo run / waypoint tolerance = 0.10 m')
ax.axis('equal'); ax.grid(alpha=0.3); ax.legend(loc='upper left'); fig.tight_layout(); fig.savefig(OUT/'trajectory.png',dpi=150)
