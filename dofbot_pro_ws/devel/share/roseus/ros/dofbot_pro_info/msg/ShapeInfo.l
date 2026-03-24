;; Auto-generated. Do not edit!


(when (boundp 'dofbot_pro_info::ShapeInfo)
  (if (not (find-package "DOFBOT_PRO_INFO"))
    (make-package "DOFBOT_PRO_INFO"))
  (shadow 'ShapeInfo (find-package "DOFBOT_PRO_INFO")))
(unless (find-package "DOFBOT_PRO_INFO::SHAPEINFO")
  (make-package "DOFBOT_PRO_INFO::SHAPEINFO"))

(in-package "ROS")
;;//! \htmlinclude ShapeInfo.msg.html


(defclass dofbot_pro_info::ShapeInfo
  :super ros::object
  :slots (_value ))

(defmethod dofbot_pro_info::ShapeInfo
  (:init
   (&key
    ((:value __value) (make-array 0 :initial-element 0.0 :element-type :float))
    )
   (send-super :init)
   (setq _value __value)
   self)
  (:value
   (&optional __value)
   (if __value (setq _value __value)) _value)
  (:serialization-length
   ()
   (+
    ;; float32[] _value
    (* 4    (length _value)) 4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; float32[] _value
     (write-long (length _value) s)
     (dotimes (i (length _value))
       (sys::poke (elt _value i) (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
       )
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; float32[] _value
   (let (n)
     (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4)
     (setq _value (instantiate float-vector n))
     (dotimes (i n)
     (setf (elt _value i) (sys::peek buf ptr- :float)) (incf ptr- 4)
     ))
   ;;
   self)
  )

(setf (get dofbot_pro_info::ShapeInfo :md5sum-) "1becc0cb8362a822e3753aa6cf42cf70")
(setf (get dofbot_pro_info::ShapeInfo :datatype-) "dofbot_pro_info/ShapeInfo")
(setf (get dofbot_pro_info::ShapeInfo :definition-)
      "float32[] value
")



(provide :dofbot_pro_info/ShapeInfo "1becc0cb8362a822e3753aa6cf42cf70")


