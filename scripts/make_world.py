"""Generate an original small differential-drive simulation; no remote assets."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def material(c):
    return f'<material><ambient>{c}</ambient><diffuse>{c}</diffuse></material>'

def box(name, pose, size, color, collision=True):
    geom = f'<geometry><box><size>{size}</size></box></geometry>'
    coll = f'<collision name="collision">{geom}</collision>' if collision else ''
    return f'<model name="{name}"><static>true</static><pose>{pose}</pose><link name="link">{coll}<visual name="visual">{geom}{material(color)}</visual></link></model>'

parts = ['''<?xml version="1.0"?>
<sdf version="1.9"><world name="step1">
<physics name="physics" type="ignored"><max_step_size>0.001</max_step_size><real_time_factor>1</real_time_factor></physics>
<plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
<plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
<plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
<plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"><render_engine>ogre2</render_engine></plugin>
<scene><ambient>0.65 0.65 0.65 1</ambient><background>0.09 0.12 0.18 1</background><shadows>false</shadows></scene>
<light name="sun" type="directional"><pose>0 0 10 0 0 0</pose><diffuse>0.85 0.85 0.85 1</diffuse><specular>0.1 0.1 0.1 1</specular><direction>-0.3 0.2 -1</direction><cast_shadows>false</cast_shadows></light>
''']
parts.append(box('floor', '1 0.8 -0.06 0 0 0', '6 5 0.1', '0.79 0.83 0.86 1'))
for name,x,y,c in [('home',0,0,'0.15 0.45 0.95 1'), ('inspection',2,0,'0.95 0.6 0.1 1'), ('supply',2,1.8,'0.15 0.75 0.45 1')]:
    parts.append(box(name, f'{x} {y} 0.002 0 0 0','0.65 0.65 0.008',c,False))
for i in range(-2,5):
    parts.append(box(f'grid_x{i}',f'{i} 0.8 -0.003 0 0 0','0.012 5 0.004','0.55 0.6 0.65 1',False))
for i in range(-1,4):
    parts.append(box(f'grid_y{i}',f'1 {i} -0.003 0 0 0','6 0.012 0.004','0.55 0.6 0.65 1',False))
parts.append('''<model name="robot"><pose>0 0 0.13 0 0 0</pose>
<link name="base_link"><inertial><mass>3</mass><inertia><ixx>0.05</ixx><iyy>0.06</iyy><izz>0.08</izz></inertia></inertial>
<collision name="body"><geometry><box><size>0.44 0.3 0.14</size></box></geometry></collision>
<visual name="body"><geometry><box><size>0.44 0.3 0.14</size></box></geometry><material><ambient>0.07 0.18 0.3 1</ambient><diffuse>0.07 0.18 0.3 1</diffuse></material></visual>
<visual name="nose"><pose>0.2 0 0.09 0 0 0</pose><geometry><box><size>0.05 0.24 0.03</size></box></geometry><material><ambient>1 0.35 0.1 1</ambient><diffuse>1 0.35 0.1 1</diffuse></material></visual></link>''')
for name,y in [('left',0.19),('right',-0.19)]:
    parts.append(f'''<link name="{name}_wheel"><pose>0 {y} -0.03 1.57079632679 0 0</pose>
<inertial><mass>0.3</mass><inertia><ixx>0.0008</ixx><iyy>0.0008</iyy><izz>0.0015</izz></inertia></inertial>
<collision name="collision"><geometry><cylinder><radius>0.1</radius><length>0.05</length></cylinder></geometry></collision>
<visual name="visual"><geometry><cylinder><radius>0.1</radius><length>0.05</length></cylinder></geometry>{material('0.08 0.08 0.08 1')}</visual></link>
<joint name="{name}_joint" type="revolute"><parent>base_link</parent><child>{name}_wheel</child><axis><xyz expressed_in="__model__">0 1 0</xyz><limit><lower>-1e16</lower><upper>1e16</upper></limit></axis></joint>''')
for name,x in [('front',0.17),('back',-0.17)]:
    parts.append(f'''<link name="{name}_caster"><pose>{x} 0 -0.1 0 0 0</pose><inertial><mass>0.05</mass><inertia><ixx>0.00002</ixx><iyy>0.00002</iyy><izz>0.00002</izz></inertia></inertial><collision name="collision"><geometry><sphere><radius>0.03</radius></sphere></geometry><surface><friction><ode><mu>0</mu><mu2>0</mu2></ode></friction></surface></collision><visual name="visual"><geometry><sphere><radius>0.03</radius></sphere></geometry></visual></link><joint name="{name}_joint" type="fixed"><parent>base_link</parent><child>{name}_caster</child></joint>''')
parts.append('''<plugin filename="gz-sim-diff-drive-system" name="gz::sim::systems::DiffDrive"><left_joint>left_joint</left_joint><right_joint>right_joint</right_joint><wheel_separation>0.38</wheel_separation><wheel_radius>0.1</wheel_radius><topic>/cmd_vel</topic><odom_topic>/wheel_odom</odom_topic><odom_publish_frequency>30</odom_publish_frequency></plugin>
<plugin filename="gz-sim-odometry-publisher-system" name="gz::sim::systems::OdometryPublisher"><odom_topic>/odom</odom_topic><odom_frame>world</odom_frame><robot_base_frame>robot/base_link</robot_base_frame><dimensions>2</dimensions><odom_publish_frequency>30</odom_publish_frequency></plugin>
</model>
<model name="overhead"><static>true</static><pose>1 0.9 7 0 1.57079632679 0</pose><link name="camera_link"><sensor name="camera" type="camera"><always_on>true</always_on><update_rate>10</update_rate><topic>/camera</topic><camera><horizontal_fov>0.95</horizontal_fov><image><width>960</width><height>640</height><format>R8G8B8</format></image><clip><near>0.1</near><far>100</far></clip></camera></sensor></link></model>
</world></sdf>''')
(ROOT/'world').mkdir(exist_ok=True)
(ROOT/'world/step1.sdf').write_text('\n'.join(parts), encoding='utf-8')
print(ROOT/'world/step1.sdf')
