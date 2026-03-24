; Auto-generated. Do not edit!


(cl:in-package yahboomcar_msgs-msg)


;//! \htmlinclude CurrentArmState.msg.html

(cl:defclass <CurrentArmState> (roslisp-msg-protocol:ros-message)
  ((joint
    :reader joint
    :initarg :joint
    :type (cl:vector cl:float)
   :initform (cl:make-array 6 :element-type 'cl:float :initial-element 0.0))
   (Pose
    :reader Pose
    :initarg :Pose
    :type (cl:vector cl:float)
   :initform (cl:make-array 6 :element-type 'cl:float :initial-element 0.0))
   (arm_error
    :reader arm_error
    :initarg :arm_error
    :type cl:integer
    :initform 0)
   (sys_err
    :reader sys_err
    :initarg :sys_err
    :type cl:integer
    :initform 0))
)

(cl:defclass CurrentArmState (<CurrentArmState>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <CurrentArmState>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'CurrentArmState)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name yahboomcar_msgs-msg:<CurrentArmState> is deprecated: use yahboomcar_msgs-msg:CurrentArmState instead.")))

(cl:ensure-generic-function 'joint-val :lambda-list '(m))
(cl:defmethod joint-val ((m <CurrentArmState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yahboomcar_msgs-msg:joint-val is deprecated.  Use yahboomcar_msgs-msg:joint instead.")
  (joint m))

(cl:ensure-generic-function 'Pose-val :lambda-list '(m))
(cl:defmethod Pose-val ((m <CurrentArmState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yahboomcar_msgs-msg:Pose-val is deprecated.  Use yahboomcar_msgs-msg:Pose instead.")
  (Pose m))

(cl:ensure-generic-function 'arm_error-val :lambda-list '(m))
(cl:defmethod arm_error-val ((m <CurrentArmState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yahboomcar_msgs-msg:arm_error-val is deprecated.  Use yahboomcar_msgs-msg:arm_error instead.")
  (arm_error m))

(cl:ensure-generic-function 'sys_err-val :lambda-list '(m))
(cl:defmethod sys_err-val ((m <CurrentArmState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yahboomcar_msgs-msg:sys_err-val is deprecated.  Use yahboomcar_msgs-msg:sys_err instead.")
  (sys_err m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <CurrentArmState>) ostream)
  "Serializes a message object of type '<CurrentArmState>"
  (cl:map cl:nil #'(cl:lambda (ele) (cl:let ((bits (roslisp-utils:encode-single-float-bits ele)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream)))
   (cl:slot-value msg 'joint))
  (cl:map cl:nil #'(cl:lambda (ele) (cl:let ((bits (roslisp-utils:encode-single-float-bits ele)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream)))
   (cl:slot-value msg 'Pose))
  (cl:let* ((signed (cl:slot-value msg 'arm_error)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'sys_err)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <CurrentArmState>) istream)
  "Deserializes a message object of type '<CurrentArmState>"
  (cl:setf (cl:slot-value msg 'joint) (cl:make-array 6))
  (cl:let ((vals (cl:slot-value msg 'joint)))
    (cl:dotimes (i 6)
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:aref vals i) (roslisp-utils:decode-single-float-bits bits)))))
  (cl:setf (cl:slot-value msg 'Pose) (cl:make-array 6))
  (cl:let ((vals (cl:slot-value msg 'Pose)))
    (cl:dotimes (i 6)
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:aref vals i) (roslisp-utils:decode-single-float-bits bits)))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'arm_error) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'sys_err) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<CurrentArmState>)))
  "Returns string type for a message object of type '<CurrentArmState>"
  "yahboomcar_msgs/CurrentArmState")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'CurrentArmState)))
  "Returns string type for a message object of type 'CurrentArmState"
  "yahboomcar_msgs/CurrentArmState")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<CurrentArmState>)))
  "Returns md5sum for a message object of type '<CurrentArmState>"
  "e5f27c48b1091d6a03004a33ae1aa8e0")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'CurrentArmState)))
  "Returns md5sum for a message object of type 'CurrentArmState"
  "e5f27c48b1091d6a03004a33ae1aa8e0")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<CurrentArmState>)))
  "Returns full string definition for message of type '<CurrentArmState>"
  (cl:format cl:nil "float32[6] joint~%float32[6] Pose~%int32 arm_error~%int32 sys_err~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'CurrentArmState)))
  "Returns full string definition for message of type 'CurrentArmState"
  (cl:format cl:nil "float32[6] joint~%float32[6] Pose~%int32 arm_error~%int32 sys_err~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <CurrentArmState>))
  (cl:+ 0
     0 (cl:reduce #'cl:+ (cl:slot-value msg 'joint) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ 4)))
     0 (cl:reduce #'cl:+ (cl:slot-value msg 'Pose) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ 4)))
     4
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <CurrentArmState>))
  "Converts a ROS message object to a list"
  (cl:list 'CurrentArmState
    (cl:cons ':joint (joint msg))
    (cl:cons ':Pose (Pose msg))
    (cl:cons ':arm_error (arm_error msg))
    (cl:cons ':sys_err (sys_err msg))
))
