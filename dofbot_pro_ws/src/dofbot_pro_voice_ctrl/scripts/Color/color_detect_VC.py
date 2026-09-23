#!/usr/bin/env python
# -*- coding: utf-8 -*-
print("语音指令词如下：")
print("------分拣红色块、分拣绿色块、分拣蓝色块、分拣黄色块------")
import os
# Run without a display when DISPLAY is not set (e.g. SSH headless).
_HEADLESS = (os.environ.get("DISPLAY", "") == "")
if _HEADLESS:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
print("[color_detect] headless mode:", _HEADLESS)
import cv2
import rospy
import numpy as np
from sensor_msgs.msg import Image
import message_filters
from std_msgs.msg import Float32,Bool,Int8
from cv_bridge import CvBridge
import cv2 as cv
encoding = ['16UC1', '32FC1']
import time
#color recognition
from astra_common import *
from dynamic_reconfigure.server import Server
from dynamic_reconfigure.client import Client
import rospkg
from dofbot_pro_voice_ctrl.cfg import ColorHSVConfig
import math
from dofbot_pro_info.msg import *


class ColorDetect:
    def __init__(self):
        nodeName = 'color_detect'
        rospy.init_node(nodeName)

        self.init_joints = [90.0, 120, 0.0, 0.0, 90, 30]
        
        self.pub_ColorInfo = rospy.Publisher("xyz", Position, queue_size=1)
        self.pubPoint = rospy.Publisher("TargetAngle", ArmJoint, queue_size=1)
        self.grasp_status_sub = rospy.Subscriber('grasp_done', Bool, self.GraspStatusCallback, queue_size=1)
        self.sub_voice = rospy.Subscriber('voice_result', Int8, self.getVoiceResultCallback, queue_size=1)
        self.depth_image_sub = message_filters.Subscriber('/camera/depth/image_raw',Image)
        self.rgb_image_sub = message_filters.Subscriber('/camera/color/image_raw',Image)
        self.pub_playID = rospy.Publisher("player_id", Int8, queue_size=1)
        self.TimeSynchronizer = message_filters.ApproximateTimeSynchronizer([self.rgb_image_sub,self.depth_image_sub],10,0.5)
        self.TimeSynchronizer.registerCallback(self.TrackAndGrap)
        self.y = 320 #320
        self.x = 240 #240
        self.pr_time = time.time()

        self.rgb_bridge = CvBridge()
        self.depth_bridge = CvBridge()

        #color
        self.Roi_init = ()
        self.hsv_range = ()
        self.circle = (0, 0, 0)
        self.dyn_update = False
        self.select_flags = False
        self.gTracker_state = False
        self.windows_name = 'frame'
        self.Track_state = 'init'
        self.color_list = ['red','green','blue','yellow']
        self.index = 0
        self.color = color_detect()
        self.cols, self.rows = 0, 0
        self.Mouse_XY = (0, 0)
        self.cx = 0
        self.cy = 0
        self.target_color = 'red'
        self.play_id = Int8()
        self.red_hsv_text = rospkg.RosPack().get_path("dofbot_pro_voice_ctrl") + "/scripts/Color/red_colorHSV.text"
        self.green_hsv_text = rospkg.RosPack().get_path("dofbot_pro_voice_ctrl") + "/scripts/Color/green_colorHSV.text"
        self.blue_hsv_text = rospkg.RosPack().get_path("dofbot_pro_voice_ctrl") + "/scripts/Color/blue_colorHSV.text"
        self.yellow_hsv_text = rospkg.RosPack().get_path("dofbot_pro_voice_ctrl") + "/scripts/Color/yellow_colorHSV.text"
        # Clear stale dyn_reconfigure cache BEFORE creating the Server,
        # so the callback fires with defaults, not old cached HSV values.
        os.system('rosparam delete /color_detect 2>/dev/null || true')
        Server(ColorHSVConfig, self.dynamic_reconfigure_callback)
        self.dyn_client = Client(nodeName, timeout=60)

        self.circle_r = 0 #防止误识别到其他的杂乱的点
        self.pubPos_flag = False
        exit_code = os.system('rosservice call /camera/set_color_exposure  50')


 
    def GraspStatusCallback(self,msg):
        if msg.data == True:
            
            if self.target_color == 'red':
                self.play_id.data = 18
                self.pub_playID.publish(self.play_id) 
                
            elif self.target_color == 'green':
                self.play_id.data = 19
                self.pub_playID.publish(self.play_id)
                
            elif self.target_color == 'blue':
                self.play_id.data = 20
                self.pub_playID.publish(self.play_id)
                
            elif self.target_color == 'yellow':
                self.play_id.data = 21
                self.pub_playID.publish(self.play_id)
            # Single-shot mode: do NOT re-arm detection after completing a grasp
            self.pubPos_flag = False
            self.Track_state = 'init'
            self.cx = 0
            self.cy = 0
            self.circle_r = 0
            rospy.loginfo("[color_detect] Grasp completed for %s. Resetting to standby (single-shot).", self.target_color)

    def getVoiceResultCallback(self,msg): 
        if msg.data == 7:
            self.target_color = "red"
            self.pubPos_flag = True
        elif msg.data == 8:
            self.target_color = "green"
            self.pubPos_flag = True
        elif msg.data == 9:
            self.target_color = "blue"
            self.pubPos_flag = True
        elif msg.data == 10:
            self.target_color = "yellow"
            self.pubPos_flag = True
        print("Get the target color is ",self.target_color)
        self.Track_state = "identify"
        # Do NOT push to dyn_reconfigure — let the file values take effect directly
        self.dyn_update = False

        
        
            
    
    def dynamic_reconfigure_callback(self, config, level):
        # Update the in-memory HSV range from the GUI sliders only when NOT in voice identify mode.
        # In identify mode, the calibrated .text files are the authority.
        if self.Track_state != 'identify':
            if self.target_color == 'red':
                self.hsv_range = ((config['R_Hmin'], config['R_Smin'], config['R_Vmin']),
                                  (config['R_Hmax'], config['R_Smax'], config['R_Vmax']))
            elif self.target_color == 'green':
                self.hsv_range = ((config['G_Hmin'], config['G_Smin'], config['G_Vmin']),
                                  (config['G_Hmax'], config['G_Smax'], config['G_Vmax']))
            elif self.target_color == 'blue':
                self.hsv_range = ((config['B_Hmin'], config['B_Smin'], config['B_Vmin']),
                                  (config['B_Hmax'], config['B_Smax'], config['B_Vmax']))
            elif self.target_color == 'yellow':
                self.hsv_range = ((config['Y_Hmin'], config['Y_Smin'], config['Y_Vmin']),
                                  (config['Y_Hmax'], config['Y_Smax'], config['Y_Vmax']))
        return config     

    def onMouse(self, event, x, y, flags, param):
        if event == 1:
            self.Track_state = 'init'
            self.select_flags = True
            self.Mouse_XY = (x, y)
        if event == 4:
            self.select_flags = False
            self.Track_state = 'mouse'
        if self.select_flags == True:
            self.cols = min(self.Mouse_XY[0], x), min(self.Mouse_XY[1], y)
            self.rows = max(self.Mouse_XY[0], x), max(self.Mouse_XY[1], y)
            self.Roi_init = (self.cols[0], self.cols[1], self.rows[0], self.rows[1])

    
    def TrackAndGrap(self,color_frame,depth_frame):
        #rgb_image
        rgb_image = self.rgb_bridge.imgmsg_to_cv2(color_frame,'bgr8')
        result_image = np.copy(rgb_image)
        #depth_image
        depth_image = self.depth_bridge.imgmsg_to_cv2(depth_frame, encoding[1])
        frame = cv.resize(depth_image, (640, 480))
        depth_image_info = frame.astype(np.float32)
        action = 0 if _HEADLESS else (cv.waitKey(10) & 0xFF)
        result_image = cv.resize(result_image, (640, 480))
        result_frame, binary = self.process(result_image, action)
        if not _HEADLESS:
            depth_to_color_image = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
            cv2.circle(depth_to_color_image, (int(self.cx), int(self.cy)), 1, (255,255,255), 10)
        
        if self.cx!=0 and self.cy!=0 and self.circle_r>15:
            if self.cx<=640 or self.cy <=480:
                center_x, center_y = self.cx,self.cy
                self.x = int(center_x)
                self.y = int(center_y)
                pos = Position()
                pos.x = center_x
                pos.y = center_y
                # Sample a 7x7 patch around (cx, cy) to avoid zero/glare on a single pixel
                patch = depth_image_info[max(0, self.y-3):min(depth_image_info.shape[0], self.y+4),
                                         max(0, self.x-3):min(depth_image_info.shape[1], self.x+4)]
                valid_depths = patch[patch > 0]
                if len(valid_depths) > 0:
                    pos.z = float(np.median(valid_depths)) / 1000.0
                else:
                    pos.z = float(depth_image_info[self.y, self.x]) / 1000.0

                if self.pubPos_flag == True:
                    # Save annotated debug frame for user
                    try:
                        os.makedirs('/home/jetson/echris/dofbot-controller/debug_output', exist_ok=True)
                        dbg = result_image.copy()
                        cv.circle(dbg, (int(self.cx), int(self.cy)), int(self.circle_r), (0, 255, 0), 2)
                        cv.circle(dbg, (int(self.cx), int(self.cy)), 5, (0, 0, 255), -1)
                        status_str = f"x={pos.x:.0f} y={pos.y:.0f} z={pos.z:.3f}m"
                        if pos.z == 0:
                            status_str += " (WARNING: DEPTH=0, TOO CLOSE!)"
                        cv.putText(dbg, status_str, (15, 35), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv.imwrite('/home/jetson/echris/dofbot-controller/debug_output/last_detection.jpg', dbg)
                    except Exception as e:
                        pass

                    if pos.z == 0.0:
                        rospy.logwarn("[color_detect] Detected at (%.0f, %.0f) but depth is 0.0m! Cube is too close (<30cm) to camera.",
                                      pos.x, pos.y)
                    else:
                        rospy.loginfo("[color_detect] Publishing xyz: x=%.1f y=%.1f z=%.3f",
                                      pos.x, pos.y, pos.z)
                        self.pub_ColorInfo.publish(pos)
                        self.pubPos_flag = False
                    
        cur_time = time.time()
        fps = str(int(1/(cur_time - self.pr_time)))
        self.pr_time = cur_time
        if not _HEADLESS:
            cv2.putText(result_frame, fps, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv.putText(result_frame, self.target_color, (50,50), cv.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 1, cv.LINE_AA)
            if len(binary) != 0:
                cv.imshow(self.windows_name, ManyImgs(1, ([result_frame, binary])))
            else:
                cv.imshow(self.windows_name, result_frame)
            cv2.imshow("depth_image", depth_to_color_image)

    def process(self, rgb_img, action):
        rospy.loginfo_throttle(2.0, "[detect] Track_state=%s target=%s hsv_range=%s",
                               self.Track_state, self.target_color, str(self.hsv_range))
        rgb_img = cv.resize(rgb_img, (640, 480))
        binary = []
        #if action == 32: self.pubPos_flag = True
        if action == ord('i') or action == ord('I'): self.Track_state = "identify"
        elif action == ord('r') or action == ord('R'): self.Reset()
        elif action == ord('f') or action == ord('F'):
            self.index = self.index + 1
            if self.index == 4:
                self.index = 0
            self.target_color = self.color_list[self.index]
        #elif action == ord('q') or action == ord('Q'): self.cancel()
        if self.Track_state == 'init':
            if not _HEADLESS:
                cv.namedWindow(self.windows_name, cv.WINDOW_AUTOSIZE)
                cv.setMouseCallback(self.windows_name, self.onMouse, 0)
            if self.select_flags == True:
                cv.line(rgb_img, self.cols, self.rows, (255, 0, 0), 2)
                cv.rectangle(rgb_img, self.cols, self.rows, (0, 255, 0), 2)
                if self.Roi_init[0] != self.Roi_init[2] and self.Roi_init[1] != self.Roi_init[3]:
                    rgb_img, self.hsv_range = self.color.Roi_hsv(rgb_img, self.Roi_init)
                    self.gTracker_state = True
                    self.dyn_update = True
                else: self.Track_state = 'init'
        elif self.Track_state == "identify":
            if os.path.exists(self.red_hsv_text) and self.target_color == 'red':
                self.hsv_range = read_HSV(self.red_hsv_text)
            elif os.path.exists(self.green_hsv_text) and self.target_color == 'green':
                self.hsv_range = read_HSV(self.green_hsv_text)
            elif os.path.exists(self.blue_hsv_text) and self.target_color == 'blue':
                self.hsv_range = read_HSV(self.blue_hsv_text)
            elif os.path.exists(self.yellow_hsv_text) and self.target_color == 'yellow':
                self.hsv_range = read_HSV(self.yellow_hsv_text)
            else: self.Track_state = 'init'
        if self.Track_state != 'init':
            if len(self.hsv_range) != 0:
                rgb_img, binary, self.circle,_ = self.color.object_follow(rgb_img, self.hsv_range)
                self.cx = self.circle[0]
                self.cy = self.circle[1]
                self.circle_r = self.circle[2]
                # Debug: always show what we see
                rospy.loginfo_throttle(1.0,
                    "[detect] cx=%.0f cy=%.0f r=%.0f (need r>15 and pubPos=%s)",
                    self.cx, self.cy, self.circle_r, self.pubPos_flag)
                if self.dyn_update == True:
                    if self.target_color == 'red':
                        write_HSV(self.red_hsv_text, self.hsv_range)
                        params = {'R_Hmin': self.hsv_range[0][0], 'R_Hmax': self.hsv_range[1][0],
                                  'R_Smin': self.hsv_range[0][1], 'R_Smax': self.hsv_range[1][1],
                                  'R_Vmin': self.hsv_range[0][2], 'R_Vmax': self.hsv_range[1][2]}
                        self.dyn_client.update_configuration(params)
                        self.dyn_update = False
                    
                    if self.target_color == 'green':
                        write_HSV(self.red_hsv_text, self.hsv_range)
                        params = {'G_Hmin': self.hsv_range[0][0], 'G_Hmax': self.hsv_range[1][0],
                                  'G_Smin': self.hsv_range[0][1], 'G_Smax': self.hsv_range[1][1],
                                  'G_Vmin': self.hsv_range[0][2], 'G_Vmax': self.hsv_range[1][2]}
                        self.dyn_client.update_configuration(params)
                        self.dyn_update = False
                    
                    if self.target_color == 'blue':
                        write_HSV(self.red_hsv_text, self.hsv_range)
                        params = {'B_Hmin': self.hsv_range[0][0], 'B_Hmax': self.hsv_range[1][0],
                                  'B_Smin': self.hsv_range[0][1], 'B_Smax': self.hsv_range[1][1],
                                  'B_Vmin': self.hsv_range[0][2], 'B_Vmax': self.hsv_range[1][2]}
                        self.dyn_client.update_configuration(params)
                        self.dyn_update = False
                    
                    if self.target_color == 'yellow':
                        write_HSV(self.red_hsv_text, self.hsv_range)
                        params = {'Y_Hmin': self.hsv_range[0][0], 'Y_Hmax': self.hsv_range[1][0],
                                  'Y_Smin': self.hsv_range[0][1], 'Y_Smax': self.hsv_range[1][1],
                                  'Y_Vmin': self.hsv_range[0][2], 'Y_Vmax': self.hsv_range[1][2]}
                        self.dyn_client.update_configuration(params)
                        self.dyn_update = False                    
        

        return rgb_img, binary

    def Reset(self):
        self.hsv_range = ()
        self.circle = (0, 0, 0)
        self.Mouse_XY = (0, 0)
        self.Track_state = 'init'
        self.init_joints = [90.0, 120, 0.0, 0.0, 90, 30]
        #self.dofbot_tracker.pub_arm(self.init_joints)
        self.cx = 0
        self.cy = 0
        self.pubPos_flag = False
        

    def calculate_yaw(self,bin_img):
        contours = cv.findContours(bin_img, cv.RETR_EXTERNAL,cv.CHAIN_APPROX_NONE)[-2]
        c = max(contours, key = cv.contourArea)
        area = math.fabs(cv.contourArea(c))
        rect = cv.minAreaRect(c)
        

    def pub_arm(self, joints, id=6, angle=180, runtime=1500):
        arm_joint = ArmJoint()
        arm_joint.id = id
        arm_joint.angle = angle
        arm_joint.run_time = runtime
        if len(joints) != 0: arm_joint.joints = joints
        else: arm_joint.joints = []
        self.pubPoint.publish(arm_joint)

if __name__ == '__main__':
    try:
        color_detect = ColorDetect()
        color_detect.pub_arm(color_detect.init_joints)
        rospy.spin()
    except Exception as e:
        rospy.logerr(str(e))

