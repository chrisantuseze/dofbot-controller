;; Auto-generated. Do not edit!


(when (boundp 'dofbot_pro_info::joint_info)
  (if (not (find-package "DOFBOT_PRO_INFO"))
    (make-package "DOFBOT_PRO_INFO"))
  (shadow 'joint_info (find-package "DOFBOT_PRO_INFO")))
(unless (find-package "DOFBOT_PRO_INFO::JOINT_INFO")
  (make-package "DOFBOT_PRO_INFO::JOINT_INFO"))

(in-package "ROS")
;;//! \htmlinclude joint_info.msg.html


(defclass dofbot_pro_info::joint_info
  :super ros::object
  :slots (_name _joint1 _joint2 _joint3 _joint4 _joint5 _joint6 ))

(defmethod dofbot_pro_info::joint_info
  (:init
   (&key
    ((:name __name) "")
    ((:joint1 __joint1) 0.0)
    ((:joint2 __joint2) 0.0)
    ((:joint3 __joint3) 0.0)
    ((:joint4 __joint4) 0.0)
    ((:joint5 __joint5) 0.0)
    ((:joint6 __joint6) 0.0)
    )
   (send-super :init)
   (setq _name (string __name))
   (setq _joint1 (float __joint1))
   (setq _joint2 (float __joint2))
   (setq _joint3 (float __joint3))
   (setq _joint4 (float __joint4))
   (setq _joint5 (float __joint5))
   (setq _joint6 (float __joint6))
   self)
  (:name
   (&optional __name)
   (if __name (setq _name __name)) _name)
  (:joint1
   (&optional __joint1)
   (if __joint1 (setq _joint1 __joint1)) _joint1)
  (:joint2
   (&optional __joint2)
   (if __joint2 (setq _joint2 __joint2)) _joint2)
  (:joint3
   (&optional __joint3)
   (if __joint3 (setq _joint3 __joint3)) _joint3)
  (:joint4
   (&optional __joint4)
   (if __joint4 (setq _joint4 __joint4)) _joint4)
  (:joint5
   (&optional __joint5)
   (if __joint5 (setq _joint5 __joint5)) _joint5)
  (:joint6
   (&optional __joint6)
   (if __joint6 (setq _joint6 __joint6)) _joint6)
  (:serialization-length
   ()
   (+
    ;; string _name
    4 (length _name)
    ;; float64 _joint1
    8
    ;; float64 _joint2
    8
    ;; float64 _joint3
    8
    ;; float64 _joint4
    8
    ;; float64 _joint5
    8
    ;; float64 _joint6
    8
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _name
       (write-long (length _name) s) (princ _name s)
     ;; float64 _joint1
       (sys::poke _joint1 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _joint2
       (sys::poke _joint2 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _joint3
       (sys::poke _joint3 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _joint4
       (sys::poke _joint4 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _joint5
       (sys::poke _joint5 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _joint6
       (sys::poke _joint6 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _name
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _name (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; float64 _joint1
     (setq _joint1 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _joint2
     (setq _joint2 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _joint3
     (setq _joint3 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _joint4
     (setq _joint4 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _joint5
     (setq _joint5 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _joint6
     (setq _joint6 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;;
   self)
  )

(setf (get dofbot_pro_info::joint_info :md5sum-) "3e4c5975a569a0944e360fbd0ea6d70a")
(setf (get dofbot_pro_info::joint_info :datatype-) "dofbot_pro_info/joint_info")
(setf (get dofbot_pro_info::joint_info :definition-)
      "string  name
float64 joint1
float64 joint2
float64 joint3
float64 joint4
float64 joint5
float64 joint6
")



(provide :dofbot_pro_info/joint_info "3e4c5975a569a0944e360fbd0ea6d70a")


