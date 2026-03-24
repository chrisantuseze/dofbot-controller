;; Auto-generated. Do not edit!


(when (boundp 'dofbot_pro_info::AprilTagInfo)
  (if (not (find-package "DOFBOT_PRO_INFO"))
    (make-package "DOFBOT_PRO_INFO"))
  (shadow 'AprilTagInfo (find-package "DOFBOT_PRO_INFO")))
(unless (find-package "DOFBOT_PRO_INFO::APRILTAGINFO")
  (make-package "DOFBOT_PRO_INFO::APRILTAGINFO"))

(in-package "ROS")
;;//! \htmlinclude AprilTagInfo.msg.html


(defclass dofbot_pro_info::AprilTagInfo
  :super ros::object
  :slots (_id _x _y _z ))

(defmethod dofbot_pro_info::AprilTagInfo
  (:init
   (&key
    ((:id __id) 0)
    ((:x __x) 0.0)
    ((:y __y) 0.0)
    ((:z __z) 0.0)
    )
   (send-super :init)
   (setq _id (round __id))
   (setq _x (float __x))
   (setq _y (float __y))
   (setq _z (float __z))
   self)
  (:id
   (&optional __id)
   (if __id (setq _id __id)) _id)
  (:x
   (&optional __x)
   (if __x (setq _x __x)) _x)
  (:y
   (&optional __y)
   (if __y (setq _y __y)) _y)
  (:z
   (&optional __z)
   (if __z (setq _z __z)) _z)
  (:serialization-length
   ()
   (+
    ;; int16 _id
    2
    ;; float32 _x
    4
    ;; float32 _y
    4
    ;; float32 _z
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int16 _id
       (write-word _id s)
     ;; float32 _x
       (sys::poke _x (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _y
       (sys::poke _y (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _z
       (sys::poke _z (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int16 _id
     (setq _id (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;; float32 _x
     (setq _x (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _y
     (setq _y (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _z
     (setq _z (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get dofbot_pro_info::AprilTagInfo :md5sum-) "d20216eb5e284a7b38d57a68c4a62b25")
(setf (get dofbot_pro_info::AprilTagInfo :datatype-) "dofbot_pro_info/AprilTagInfo")
(setf (get dofbot_pro_info::AprilTagInfo :definition-)
      "int16 id
float32 x
float32 y
float32 z
")



(provide :dofbot_pro_info/AprilTagInfo "d20216eb5e284a7b38d57a68c4a62b25")


