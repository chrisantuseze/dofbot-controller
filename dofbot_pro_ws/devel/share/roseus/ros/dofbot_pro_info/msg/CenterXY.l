;; Auto-generated. Do not edit!


(when (boundp 'dofbot_pro_info::CenterXY)
  (if (not (find-package "DOFBOT_PRO_INFO"))
    (make-package "DOFBOT_PRO_INFO"))
  (shadow 'CenterXY (find-package "DOFBOT_PRO_INFO")))
(unless (find-package "DOFBOT_PRO_INFO::CENTERXY")
  (make-package "DOFBOT_PRO_INFO::CENTERXY"))

(in-package "ROS")
;;//! \htmlinclude CenterXY.msg.html


(defclass dofbot_pro_info::CenterXY
  :super ros::object
  :slots (_center_x _center_y ))

(defmethod dofbot_pro_info::CenterXY
  (:init
   (&key
    ((:center_x __center_x) 0.0)
    ((:center_y __center_y) 0.0)
    )
   (send-super :init)
   (setq _center_x (float __center_x))
   (setq _center_y (float __center_y))
   self)
  (:center_x
   (&optional __center_x)
   (if __center_x (setq _center_x __center_x)) _center_x)
  (:center_y
   (&optional __center_y)
   (if __center_y (setq _center_y __center_y)) _center_y)
  (:serialization-length
   ()
   (+
    ;; float32 _center_x
    4
    ;; float32 _center_y
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; float32 _center_x
       (sys::poke _center_x (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _center_y
       (sys::poke _center_y (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; float32 _center_x
     (setq _center_x (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _center_y
     (setq _center_y (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get dofbot_pro_info::CenterXY :md5sum-) "c51e51b1031fa051202f8de7f01927c6")
(setf (get dofbot_pro_info::CenterXY :datatype-) "dofbot_pro_info/CenterXY")
(setf (get dofbot_pro_info::CenterXY :definition-)
      "float32 center_x
float32 center_y
")



(provide :dofbot_pro_info/CenterXY "c51e51b1031fa051202f8de7f01927c6")


