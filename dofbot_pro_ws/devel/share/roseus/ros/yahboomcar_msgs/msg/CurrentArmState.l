;; Auto-generated. Do not edit!


(when (boundp 'yahboomcar_msgs::CurrentArmState)
  (if (not (find-package "YAHBOOMCAR_MSGS"))
    (make-package "YAHBOOMCAR_MSGS"))
  (shadow 'CurrentArmState (find-package "YAHBOOMCAR_MSGS")))
(unless (find-package "YAHBOOMCAR_MSGS::CURRENTARMSTATE")
  (make-package "YAHBOOMCAR_MSGS::CURRENTARMSTATE"))

(in-package "ROS")
;;//! \htmlinclude CurrentArmState.msg.html


(defclass yahboomcar_msgs::CurrentArmState
  :super ros::object
  :slots (_joint _Pose _arm_error _sys_err ))

(defmethod yahboomcar_msgs::CurrentArmState
  (:init
   (&key
    ((:joint __joint) (make-array 6 :initial-element 0.0 :element-type :float))
    ((:Pose __Pose) (make-array 6 :initial-element 0.0 :element-type :float))
    ((:arm_error __arm_error) 0)
    ((:sys_err __sys_err) 0)
    )
   (send-super :init)
   (setq _joint __joint)
   (setq _Pose __Pose)
   (setq _arm_error (round __arm_error))
   (setq _sys_err (round __sys_err))
   self)
  (:joint
   (&optional __joint)
   (if __joint (setq _joint __joint)) _joint)
  (:Pose
   (&optional __Pose)
   (if __Pose (setq _Pose __Pose)) _Pose)
  (:arm_error
   (&optional __arm_error)
   (if __arm_error (setq _arm_error __arm_error)) _arm_error)
  (:sys_err
   (&optional __sys_err)
   (if __sys_err (setq _sys_err __sys_err)) _sys_err)
  (:serialization-length
   ()
   (+
    ;; float32[6] _joint
    (* 4    6)
    ;; float32[6] _Pose
    (* 4    6)
    ;; int32 _arm_error
    4
    ;; int32 _sys_err
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; float32[6] _joint
     (dotimes (i 6)
       (sys::poke (elt _joint i) (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
       )
     ;; float32[6] _Pose
     (dotimes (i 6)
       (sys::poke (elt _Pose i) (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
       )
     ;; int32 _arm_error
       (write-long _arm_error s)
     ;; int32 _sys_err
       (write-long _sys_err s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; float32[6] _joint
   (dotimes (i (length _joint))
     (setf (elt _joint i) (sys::peek buf ptr- :float)) (incf ptr- 4)
     )
   ;; float32[6] _Pose
   (dotimes (i (length _Pose))
     (setf (elt _Pose i) (sys::peek buf ptr- :float)) (incf ptr- 4)
     )
   ;; int32 _arm_error
     (setq _arm_error (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; int32 _sys_err
     (setq _sys_err (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get yahboomcar_msgs::CurrentArmState :md5sum-) "e5f27c48b1091d6a03004a33ae1aa8e0")
(setf (get yahboomcar_msgs::CurrentArmState :datatype-) "yahboomcar_msgs/CurrentArmState")
(setf (get yahboomcar_msgs::CurrentArmState :definition-)
      "float32[6] joint
float32[6] Pose
int32 arm_error
int32 sys_err
")



(provide :yahboomcar_msgs/CurrentArmState "e5f27c48b1091d6a03004a33ae1aa8e0")


