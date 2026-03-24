;; Auto-generated. Do not edit!


(when (boundp 'yahboomcar_msgs::Yolov5Detect)
  (if (not (find-package "YAHBOOMCAR_MSGS"))
    (make-package "YAHBOOMCAR_MSGS"))
  (shadow 'Yolov5Detect (find-package "YAHBOOMCAR_MSGS")))
(unless (find-package "YAHBOOMCAR_MSGS::YOLOV5DETECT")
  (make-package "YAHBOOMCAR_MSGS::YOLOV5DETECT"))

(in-package "ROS")
;;//! \htmlinclude Yolov5Detect.msg.html


(defclass yahboomcar_msgs::Yolov5Detect
  :super ros::object
  :slots (_result _centerx _centery ))

(defmethod yahboomcar_msgs::Yolov5Detect
  (:init
   (&key
    ((:result __result) "")
    ((:centerx __centerx) 0.0)
    ((:centery __centery) 0.0)
    )
   (send-super :init)
   (setq _result (string __result))
   (setq _centerx (float __centerx))
   (setq _centery (float __centery))
   self)
  (:result
   (&optional __result)
   (if __result (setq _result __result)) _result)
  (:centerx
   (&optional __centerx)
   (if __centerx (setq _centerx __centerx)) _centerx)
  (:centery
   (&optional __centery)
   (if __centery (setq _centery __centery)) _centery)
  (:serialization-length
   ()
   (+
    ;; string _result
    4 (length _result)
    ;; float32 _centerx
    4
    ;; float32 _centery
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _result
       (write-long (length _result) s) (princ _result s)
     ;; float32 _centerx
       (sys::poke _centerx (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _centery
       (sys::poke _centery (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _result
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _result (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; float32 _centerx
     (setq _centerx (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _centery
     (setq _centery (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get yahboomcar_msgs::Yolov5Detect :md5sum-) "f6fde05b13d0b4d8a4f931c44fa3dda6")
(setf (get yahboomcar_msgs::Yolov5Detect :datatype-) "yahboomcar_msgs/Yolov5Detect")
(setf (get yahboomcar_msgs::Yolov5Detect :definition-)
      "string result
float32 centerx
float32 centery
")



(provide :yahboomcar_msgs/Yolov5Detect "f6fde05b13d0b4d8a4f931c44fa3dda6")


