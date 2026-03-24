;; Auto-generated. Do not edit!


(when (boundp 'dofbot_pro_info::cur_joint)
  (if (not (find-package "DOFBOT_PRO_INFO"))
    (make-package "DOFBOT_PRO_INFO"))
  (shadow 'cur_joint (find-package "DOFBOT_PRO_INFO")))
(unless (find-package "DOFBOT_PRO_INFO::CUR_JOINT")
  (make-package "DOFBOT_PRO_INFO::CUR_JOINT"))
(unless (find-package "DOFBOT_PRO_INFO::CUR_JOINTREQUEST")
  (make-package "DOFBOT_PRO_INFO::CUR_JOINTREQUEST"))
(unless (find-package "DOFBOT_PRO_INFO::CUR_JOINTRESPONSE")
  (make-package "DOFBOT_PRO_INFO::CUR_JOINTRESPONSE"))

(in-package "ROS")





(defclass dofbot_pro_info::cur_jointRequest
  :super ros::object
  :slots (_srv_joints ))

(defmethod dofbot_pro_info::cur_jointRequest
  (:init
   (&key
    ((:srv_joints __srv_joints) "")
    )
   (send-super :init)
   (setq _srv_joints (string __srv_joints))
   self)
  (:srv_joints
   (&optional __srv_joints)
   (if __srv_joints (setq _srv_joints __srv_joints)) _srv_joints)
  (:serialization-length
   ()
   (+
    ;; string _srv_joints
    4 (length _srv_joints)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _srv_joints
       (write-long (length _srv_joints) s) (princ _srv_joints s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _srv_joints
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _srv_joints (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(defclass dofbot_pro_info::cur_jointResponse
  :super ros::object
  :slots (_srv_joint1 _srv_joint2 _srv_joint3 _srv_joint4 _srv_joint5 _srv_joint6 ))

(defmethod dofbot_pro_info::cur_jointResponse
  (:init
   (&key
    ((:srv_joint1 __srv_joint1) 0.0)
    ((:srv_joint2 __srv_joint2) 0.0)
    ((:srv_joint3 __srv_joint3) 0.0)
    ((:srv_joint4 __srv_joint4) 0.0)
    ((:srv_joint5 __srv_joint5) 0.0)
    ((:srv_joint6 __srv_joint6) 0.0)
    )
   (send-super :init)
   (setq _srv_joint1 (float __srv_joint1))
   (setq _srv_joint2 (float __srv_joint2))
   (setq _srv_joint3 (float __srv_joint3))
   (setq _srv_joint4 (float __srv_joint4))
   (setq _srv_joint5 (float __srv_joint5))
   (setq _srv_joint6 (float __srv_joint6))
   self)
  (:srv_joint1
   (&optional __srv_joint1)
   (if __srv_joint1 (setq _srv_joint1 __srv_joint1)) _srv_joint1)
  (:srv_joint2
   (&optional __srv_joint2)
   (if __srv_joint2 (setq _srv_joint2 __srv_joint2)) _srv_joint2)
  (:srv_joint3
   (&optional __srv_joint3)
   (if __srv_joint3 (setq _srv_joint3 __srv_joint3)) _srv_joint3)
  (:srv_joint4
   (&optional __srv_joint4)
   (if __srv_joint4 (setq _srv_joint4 __srv_joint4)) _srv_joint4)
  (:srv_joint5
   (&optional __srv_joint5)
   (if __srv_joint5 (setq _srv_joint5 __srv_joint5)) _srv_joint5)
  (:srv_joint6
   (&optional __srv_joint6)
   (if __srv_joint6 (setq _srv_joint6 __srv_joint6)) _srv_joint6)
  (:serialization-length
   ()
   (+
    ;; float64 _srv_joint1
    8
    ;; float64 _srv_joint2
    8
    ;; float64 _srv_joint3
    8
    ;; float64 _srv_joint4
    8
    ;; float64 _srv_joint5
    8
    ;; float64 _srv_joint6
    8
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; float64 _srv_joint1
       (sys::poke _srv_joint1 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _srv_joint2
       (sys::poke _srv_joint2 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _srv_joint3
       (sys::poke _srv_joint3 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _srv_joint4
       (sys::poke _srv_joint4 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _srv_joint5
       (sys::poke _srv_joint5 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _srv_joint6
       (sys::poke _srv_joint6 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; float64 _srv_joint1
     (setq _srv_joint1 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _srv_joint2
     (setq _srv_joint2 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _srv_joint3
     (setq _srv_joint3 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _srv_joint4
     (setq _srv_joint4 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _srv_joint5
     (setq _srv_joint5 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _srv_joint6
     (setq _srv_joint6 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;;
   self)
  )

(defclass dofbot_pro_info::cur_joint
  :super ros::object
  :slots ())

(setf (get dofbot_pro_info::cur_joint :md5sum-) "7bf4e10c269e4b461f9707a22ed78be1")
(setf (get dofbot_pro_info::cur_joint :datatype-) "dofbot_pro_info/cur_joint")
(setf (get dofbot_pro_info::cur_joint :request) dofbot_pro_info::cur_jointRequest)
(setf (get dofbot_pro_info::cur_joint :response) dofbot_pro_info::cur_jointResponse)

(defmethod dofbot_pro_info::cur_jointRequest
  (:response () (instance dofbot_pro_info::cur_jointResponse :init)))

(setf (get dofbot_pro_info::cur_jointRequest :md5sum-) "7bf4e10c269e4b461f9707a22ed78be1")
(setf (get dofbot_pro_info::cur_jointRequest :datatype-) "dofbot_pro_info/cur_jointRequest")
(setf (get dofbot_pro_info::cur_jointRequest :definition-)
      "# request
string  srv_joints
---
# response
float64 srv_joint1
float64 srv_joint2
float64 srv_joint3
float64 srv_joint4
float64 srv_joint5
float64 srv_joint6

")

(setf (get dofbot_pro_info::cur_jointResponse :md5sum-) "7bf4e10c269e4b461f9707a22ed78be1")
(setf (get dofbot_pro_info::cur_jointResponse :datatype-) "dofbot_pro_info/cur_jointResponse")
(setf (get dofbot_pro_info::cur_jointResponse :definition-)
      "# request
string  srv_joints
---
# response
float64 srv_joint1
float64 srv_joint2
float64 srv_joint3
float64 srv_joint4
float64 srv_joint5
float64 srv_joint6

")



(provide :dofbot_pro_info/cur_joint "7bf4e10c269e4b461f9707a22ed78be1")


