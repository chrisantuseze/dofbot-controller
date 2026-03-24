; Auto-generated. Do not edit!


(cl:in-package dofbot_pro_info-msg)


;//! \htmlinclude ShapeInfo.msg.html

(cl:defclass <ShapeInfo> (roslisp-msg-protocol:ros-message)
  ((value
    :reader value
    :initarg :value
    :type (cl:vector cl:float)
   :initform (cl:make-array 0 :element-type 'cl:float :initial-element 0.0)))
)

(cl:defclass ShapeInfo (<ShapeInfo>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <ShapeInfo>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'ShapeInfo)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name dofbot_pro_info-msg:<ShapeInfo> is deprecated: use dofbot_pro_info-msg:ShapeInfo instead.")))

(cl:ensure-generic-function 'value-val :lambda-list '(m))
(cl:defmethod value-val ((m <ShapeInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader dofbot_pro_info-msg:value-val is deprecated.  Use dofbot_pro_info-msg:value instead.")
  (value m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <ShapeInfo>) ostream)
  "Serializes a message object of type '<ShapeInfo>"
  (cl:let ((__ros_arr_len (cl:length (cl:slot-value msg 'value))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_arr_len) ostream))
  (cl:map cl:nil #'(cl:lambda (ele) (cl:let ((bits (roslisp-utils:encode-single-float-bits ele)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream)))
   (cl:slot-value msg 'value))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <ShapeInfo>) istream)
  "Deserializes a message object of type '<ShapeInfo>"
  (cl:let ((__ros_arr_len 0))
    (cl:setf (cl:ldb (cl:byte 8 0) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) __ros_arr_len) (cl:read-byte istream))
  (cl:setf (cl:slot-value msg 'value) (cl:make-array __ros_arr_len))
  (cl:let ((vals (cl:slot-value msg 'value)))
    (cl:dotimes (i __ros_arr_len)
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:aref vals i) (roslisp-utils:decode-single-float-bits bits))))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<ShapeInfo>)))
  "Returns string type for a message object of type '<ShapeInfo>"
  "dofbot_pro_info/ShapeInfo")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ShapeInfo)))
  "Returns string type for a message object of type 'ShapeInfo"
  "dofbot_pro_info/ShapeInfo")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<ShapeInfo>)))
  "Returns md5sum for a message object of type '<ShapeInfo>"
  "1becc0cb8362a822e3753aa6cf42cf70")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'ShapeInfo)))
  "Returns md5sum for a message object of type 'ShapeInfo"
  "1becc0cb8362a822e3753aa6cf42cf70")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<ShapeInfo>)))
  "Returns full string definition for message of type '<ShapeInfo>"
  (cl:format cl:nil "float32[] value~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'ShapeInfo)))
  "Returns full string definition for message of type 'ShapeInfo"
  (cl:format cl:nil "float32[] value~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <ShapeInfo>))
  (cl:+ 0
     4 (cl:reduce #'cl:+ (cl:slot-value msg 'value) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ 4)))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <ShapeInfo>))
  "Converts a ROS message object to a list"
  (cl:list 'ShapeInfo
    (cl:cons ':value (value msg))
))
