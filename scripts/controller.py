"""ROS 2 language -> intent -> waypoint controller and honest Gazebo camera recorder."""
import argparse
import csv
import json
import math
import subprocess
import time
from pathlib import Path
import joblib
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image as RosImage
from std_msgs.msg import String
from PIL import Image, ImageDraw, ImageFont
from intent_model import ROOT, predict

GOALS={'inspection':(2.0,0.0),'supply':(2.0,1.8),'home':(0.0,0.0)}
NAMES={'inspection':'点検地点（オレンジ）','supply':'備品地点（緑）','home':'ホーム（青）','stop':'停止','unknown':'未対応の指示：停止'}
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'

class Controller(Node):
    def __init__(self, demo=False):
        super().__init__('intent_waypoint_controller')
        self.model=joblib.load(ROOT/'output/intent_model.joblib')
        self.pub=self.create_publisher(Twist,'/cmd_vel',10)
        self.create_subscription(Odometry,'/odom',self.odom,10)
        self.create_subscription(RosImage,'/camera',self.camera,qos_profile_sensor_data)
        self.create_subscription(String,'/instruction',lambda msg:self.instruction(msg.data),10)
        self.create_timer(0.05,self.control)
        self.create_timer(0.1,self.record)
        self.pose=None; self.last_odom=0; self.camera_frame=None; self.last_camera=0
        self.goal=None; self.intent='stop'; self.text='開始前：ROS 2とGazeboを接続中'
        self.confidence=0; self.state='READY'; self.v=0; self.w=0
        self.start=None; self.frame_count=0; self.last_record=0; self.last_log=0
        self.events=[]; self.reached=[]; self.demo=demo; self.phase=0; self.phase_at=0
        self.finished=False; self.fail_reason=None; self.camera_count=0; self.arrived_at=0
        self.create_timer(0.1,self.sequence)
        self.out=ROOT/'output'; self.out.mkdir(exist_ok=True)
        self.logfile=(self.out/'trajectory.csv').open('w',newline='')
        self.writer=csv.writer(self.logfile); self.writer.writerow(['wall_seconds','x','y','yaw','intent','state','linear_velocity','angular_velocity'])
        self.encoder=None
        self.font=ImageFont.truetype(FONT,24); self.small=ImageFont.truetype(FONT,19)

    def odom(self,msg):
        p=msg.pose.pose.position; q=msg.pose.pose.orientation
        self.pose=(p.x,p.y,math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)))
        self.last_odom=time.monotonic()

    def camera(self,msg):
        if msg.encoding not in ('rgb8','bgr8'): return
        raw=bytes(msg.data)
        self.camera_frame=Image.frombytes('RGB',(msg.width,msg.height),raw,'raw','RGB' if msg.encoding=='rgb8' else 'BGR',msg.step)
        self.last_camera=time.monotonic(); self.camera_count+=1

    def event(self,kind,**kwargs):
        data={'time':round(time.monotonic()-(self.start or time.monotonic()),3),'event':kind,**kwargs}
        self.events.append(data); print(json.dumps(data,ensure_ascii=False),flush=True)

    def instruction(self,text):
        self.text=text; self.intent,self.confidence=predict(self.model,text)
        self.goal=GOALS.get(self.intent); self.state='MOVING' if self.goal else 'STOPPED'
        self.event('instruction',text=text,intent=self.intent,confidence=self.confidence,goal=self.goal)
        if self.goal is None: self.send(0,0)

    def send(self,v,w):
        self.v=v; self.w=w
        msg=Twist(); msg.linear.x=float(v); msg.angular.z=float(w); self.pub.publish(msg)

    def control(self):
        now=time.monotonic()
        if self.pose is None or now-self.last_odom>1.0:
            self.send(0,0)
            if self.goal: self.state='ODOM_STALE'
            return
        if self.goal is None: self.send(0,0); return
        x,y,yaw=self.pose; gx,gy=self.goal
        distance=math.hypot(gx-x,gy-y)
        if distance<0.10:
            self.reached.append({'intent':self.intent,'position':[x,y],'error_m':distance})
            self.event('arrived',**self.reached[-1]); self.arrived_at=now; self.goal=None; self.state='ARRIVED'; self.send(0,0); return
        angle=math.atan2(gy-y,gx-x)-yaw
        error=math.atan2(math.sin(angle),math.cos(angle))
        self.state='MOVING'
        self.send(min(0.24,0.7*distance)*max(0.0,math.cos(error)) if abs(error)<0.65 else 0.0,max(-0.8,min(0.8,1.8*error)))

    def sequence(self):
        now=time.monotonic()
        if self.start is None:
            if self.pose is not None and self.camera_frame is not None:
                self.start=now; self.phase_at=now; self.event('recording_started')
            return
        if not self.demo: return
        elapsed=now-self.start
        if elapsed>165:
            self.fail_reason='Demo exceeded 165 seconds'; self.finished=True; return
        # Each instruction travels through a ROS topic before being classified.
        if not hasattr(self,'instruction_pub'): self.instruction_pub=self.create_publisher(String,'/instruction',10)
        text=None
        if self.phase==0 and now-self.phase_at>8: text='点検エリアへ移動してください'
        elif self.phase in (1,2) and self.state=='ARRIVED' and now-self.arrived_at>4:
            text='備品の場所まで進んでください' if self.phase==1 else 'ホームに戻ってください'
        elif self.phase==3 and self.state=='ARRIVED' and now-self.arrived_at>4: text='ダンスを踊って'
        elif self.phase==4 and now-self.phase_at>7: text='いったん停止してください'
        elif self.phase==5 and elapsed>=75 and now-self.phase_at>8:
            self.finished=True
        if text:
            self.instruction_pub.publish(String(data=text)); self.phase+=1; self.phase_at=now

    def record(self):
        if self.start is None or self.camera_frame is None: return
        now=time.monotonic(); elapsed=now-self.start
        canvas=Image.new('RGB',(1280,800),'#101c2b'); canvas.paste(self.camera_frame.resize((960,640)),(0,100))
        d=ImageDraw.Draw(canvas)
        d.text((24,16),'Physical AI | 日本語の指示で移動するロボット',font=self.font,fill='white')
        d.text((24,55),'ROS 2 Jazzy → ros_gz_bridge → Gazebo Harmonic（シミュレーション）',font=self.small,fill='#9fc0d5')
        lines=['AIの推論結果',NAMES[self.intent],f'分類スコア {self.confidence:.2f}', '',f'状態：{self.state}',f'経過 {elapsed:.1f} 秒',f'到着数 {len(self.reached)} / 3','',f'速度 {self.v:.2f} m/s',f'旋回 {self.w:.2f} rad/s']
        if self.pose: lines.extend(['',f'x = {self.pose[0]:.2f} m',f'y = {self.pose[1]:.2f} m'])
        for i,line in enumerate(lines): d.text((980,120+i*37),line,font=self.small,fill='white')
        d.text((24,750),f'指示：「{self.text}」',font=self.font,fill='#fbd38d')
        d.text((24,703),'Gazebo仮想カメラの実画像 ／ ローカル実行・実時間収録',font=self.small,fill='#163047')
        if now-self.last_camera>2: d.text((24,150),'CAMERA STALE',font=self.font,fill='red')
        if self.encoder is None:
            self.encoder=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1280x800','-framerate','10','-i','-','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(self.out/'demo.mp4')],stdin=subprocess.PIPE)
        # Duplicate only to preserve wall-clock duration if rendering stalls; never accelerate the run.
        expected=int(elapsed*10)+1
        while self.frame_count<expected:
            self.encoder.stdin.write(canvas.tobytes()); self.frame_count+=1
        if self.frame_count % 20 == 0: canvas.save(self.out/'latest.png')
        if elapsed-self.last_log>=0.2 and self.pose:
            self.writer.writerow([round(elapsed,3),*self.pose,self.intent,self.state,self.v,self.w]); self.last_log=elapsed
        if self.state=='ARRIVED' and self.intent in GOALS: canvas.save(self.out/f'arrival_{self.intent}.png')

    def close(self):
        for _ in range(3): self.send(0,0)
        if self.encoder:
            self.encoder.stdin.close(); self.encoder.wait(timeout=30)
        self.logfile.close()
        result={'success':self.finished and not self.fail_reason and len(self.reached)==3,
                'failure':self.fail_reason,'goals':self.reached,'events':self.events,
                'video_duration_s':self.frame_count/10,'camera_messages':self.camera_count,
                'controller':'proportional waypoint controller; AI classifies text, does not learn motion',
                'odometry_source':'Gazebo OdometryPublisher ground truth; ideal localization, not wheel encoders or SLAM',
                'environment':'obstacle-free simulated floor; no cleaning manipulation implemented'}
        (self.out/'run_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--demo',action='store_true'); args=parser.parse_args()
    rclpy.init(); node=Controller(args.demo); started=time.monotonic()
    try:
        while rclpy.ok() and not node.finished:
            rclpy.spin_once(node,timeout_sec=0.1)
            if node.start is None and time.monotonic()-started>90:
                node.fail_reason='No odometry/camera within 90 seconds'; break
    except KeyboardInterrupt: node.fail_reason='Interrupted'
    finally:
        node.close(); node.destroy_node(); rclpy.shutdown()
    if args.demo and (node.fail_reason or len(node.reached)!=3): raise SystemExit(1)

if __name__=='__main__': main()
