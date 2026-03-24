;; Auto-generated. Do not edit!


(when (boundp 'dofbot_pro_info::WidthInfo)
  (if (not (find-package "DOFBOT_PRO_INFO"))
    (make-package "DOFBOT_PRO_INFO"))
  (shadow 'WidthInfo (find-package "DOFBOT_PRO_INFO")))
(unless (find-package "DOFBOT_PRO_INFO::WIDTHINFO")
  (make-package "DOFBOT_PRO_INFO::WIDTHINFO"))

(in-package "ROS")
;;//! \htmlinclude WidthInfo.msg.html


(defclass dofbot_pro_info::WidthInfo
  :super ros::object
  :slots (_L_x _L_y _R_x _R_y ))

(defmethod dofbot_pro_info::WidthInfo
  (:init
   (&key
    ((:L_x __L_x) 0.0)
    ((:L_y __L_y) 0.0)
    ((:R_x __R_x) 0.0)
    ((:R_y __R_y) 0.0)
    )
   (send-super :init)
   (setq _L_x (float __L_x))
   (setq _L_y (float __L_y))
   (setq _R_x (float __R_x))
   (setq _R_y (float __R_y))
   self)
  (:L_x
   (&optional __L_x)
   (if __L_x (setq _L_x __L_x)) _L_x)
  (:L_y
   (&optional __L_y)
   (if __L_y (setq _L_y __L_y)) _L_y)
  (:R_x
   (&optional __R_x)
   (if __R_x (setq _R_x __R_x)) _R_x)
  (:R_y
   (&optional __R_y)
   (if __R_y (setq _R_y __R_y)) _R_y)
  (:serialization-length
   ()
   (+
    ;; float32 _L_x
    4
    ;; float32 _L_y
    4
    ;; float32 _R_x
    4
    ;; float32 _R_y
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; float32 _L_x
       (sys::poke _L_x (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _L_y
       (sys::poke _L_y (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _R_x
       (sys::poke _R_x (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _R_y
       (sys::poke _R_y (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; float32 _L_x
     (setq _L_x (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _L_y
     (setq _L_y (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _R_x
     (setq _R_x (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _R_y
     (setq _R_y (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get dofbot_pro_info::WidthInfo :md5sum-) "de9e03608448f2f1799b1dfee66084ae")
(setf (get dofbot_pro_info::WidthInfo :datatype-) "dofbot_pro_info/WidthInfo")
(setf (get dofbot_pro_info::WidthInfo :definition-)
      "float32 L_x
float32 L_y
float32 R_x
float32 R_y

")



(provide :dofbot_pro_info/WidthInfo "de9e03608448f2f1799b1dfee66084ae")


