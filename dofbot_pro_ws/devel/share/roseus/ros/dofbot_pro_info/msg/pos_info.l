;; Auto-generated. Do not edit!


(when (boundp 'dofbot_pro_info::pos_info)
  (if (not (find-package "DOFBOT_PRO_INFO"))
    (make-package "DOFBOT_PRO_INFO"))
  (shadow 'pos_info (find-package "DOFBOT_PRO_INFO")))
(unless (find-package "DOFBOT_PRO_INFO::POS_INFO")
  (make-package "DOFBOT_PRO_INFO::POS_INFO"))

(in-package "ROS")
;;//! \htmlinclude pos_info.msg.html


(defclass dofbot_pro_info::pos_info
  :super ros::object
  :slots (_name _pos1 _pos2 _pos3 _Roll _Pitch _Yaw ))

(defmethod dofbot_pro_info::pos_info
  (:init
   (&key
    ((:name __name) "")
    ((:pos1 __pos1) 0.0)
    ((:pos2 __pos2) 0.0)
    ((:pos3 __pos3) 0.0)
    ((:Roll __Roll) 0.0)
    ((:Pitch __Pitch) 0.0)
    ((:Yaw __Yaw) 0.0)
    )
   (send-super :init)
   (setq _name (string __name))
   (setq _pos1 (float __pos1))
   (setq _pos2 (float __pos2))
   (setq _pos3 (float __pos3))
   (setq _Roll (float __Roll))
   (setq _Pitch (float __Pitch))
   (setq _Yaw (float __Yaw))
   self)
  (:name
   (&optional __name)
   (if __name (setq _name __name)) _name)
  (:pos1
   (&optional __pos1)
   (if __pos1 (setq _pos1 __pos1)) _pos1)
  (:pos2
   (&optional __pos2)
   (if __pos2 (setq _pos2 __pos2)) _pos2)
  (:pos3
   (&optional __pos3)
   (if __pos3 (setq _pos3 __pos3)) _pos3)
  (:Roll
   (&optional __Roll)
   (if __Roll (setq _Roll __Roll)) _Roll)
  (:Pitch
   (&optional __Pitch)
   (if __Pitch (setq _Pitch __Pitch)) _Pitch)
  (:Yaw
   (&optional __Yaw)
   (if __Yaw (setq _Yaw __Yaw)) _Yaw)
  (:serialization-length
   ()
   (+
    ;; string _name
    4 (length _name)
    ;; float64 _pos1
    8
    ;; float64 _pos2
    8
    ;; float64 _pos3
    8
    ;; float64 _Roll
    8
    ;; float64 _Pitch
    8
    ;; float64 _Yaw
    8
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _name
       (write-long (length _name) s) (princ _name s)
     ;; float64 _pos1
       (sys::poke _pos1 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _pos2
       (sys::poke _pos2 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _pos3
       (sys::poke _pos3 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _Roll
       (sys::poke _Roll (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _Pitch
       (sys::poke _Pitch (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _Yaw
       (sys::poke _Yaw (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _name
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _name (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; float64 _pos1
     (setq _pos1 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _pos2
     (setq _pos2 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _pos3
     (setq _pos3 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _Roll
     (setq _Roll (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _Pitch
     (setq _Pitch (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _Yaw
     (setq _Yaw (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;;
   self)
  )

(setf (get dofbot_pro_info::pos_info :md5sum-) "464446b8e571013c21f5be23c938371e")
(setf (get dofbot_pro_info::pos_info :datatype-) "dofbot_pro_info/pos_info")
(setf (get dofbot_pro_info::pos_info :definition-)
      "string  name
float64 pos1
float64 pos2
float64 pos3
float64 Roll
float64 Pitch
float64 Yaw
")



(provide :dofbot_pro_info/pos_info "464446b8e571013c21f5be23c938371e")


