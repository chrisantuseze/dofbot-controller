; Auto-generated. Do not edit!


(cl:in-package yahboomcar_msgs-msg)


;//! \htmlinclude Yolov5Detect.msg.html

(cl:defclass <Yolov5Detect> (roslisp-msg-protocol:ros-message)
  ((result
    :reader result
    :initarg :result
    :type cl:string
    :initform "")
   (centerx
    :reader centerx
    :initarg :centerx
    :type cl:float
    :initform 0.0)
   (centery
    :reader centery
    :initarg :centery
    :type cl:float
    :initform 0.0))
)

(cl:defclass Yolov5Detect (<Yolov5Detect>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Yolov5Detect>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Yolov5Detect)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name yahboomcar_msgs-msg:<Yolov5Detect> is deprecated: use yahboomcar_msgs-msg:Yolov5Detect instead.")))

(cl:ensure-generic-function 'result-val :lambda-list '(m))
(cl:defmethod result-val ((m <Yolov5Detect>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yahboomcar_msgs-msg:result-val is deprecated.  Use yahboomcar_msgs-msg:result instead.")
  (result m))

(cl:ensure-generic-function 'centerx-val :lambda-list '(m))
(cl:defmethod centerx-val ((m <Yolov5Detect>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yahboomcar_msgs-msg:centerx-val is deprecated.  Use yahboomcar_msgs-msg:centerx instead.")
  (centerx m))

(cl:ensure-generic-function 'centery-val :lambda-list '(m))
(cl:defmethod centery-val ((m <Yolov5Detect>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yahboomcar_msgs-msg:centery-val is deprecated.  Use yahboomcar_msgs-msg:centery instead.")
  (centery m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Yolov5Detect>) ostream)
  "Serializes a message object of type '<Yolov5Detect>"
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'result))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'result))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'centerx))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'centery))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Yolov5Detect>) istream)
  "Deserializes a message object of type '<Yolov5Detect>"
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'result) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'result) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'centerx) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'centery) (roslisp-utils:decode-single-float-bits bits)))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Yolov5Detect>)))
  "Returns string type for a message object of type '<Yolov5Detect>"
  "yahboomcar_msgs/Yolov5Detect")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Yolov5Detect)))
  "Returns string type for a message object of type 'Yolov5Detect"
  "yahboomcar_msgs/Yolov5Detect")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Yolov5Detect>)))
  "Returns md5sum for a message object of type '<Yolov5Detect>"
  "f6fde05b13d0b4d8a4f931c44fa3dda6")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Yolov5Detect)))
  "Returns md5sum for a message object of type 'Yolov5Detect"
  "f6fde05b13d0b4d8a4f931c44fa3dda6")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Yolov5Detect>)))
  "Returns full string definition for message of type '<Yolov5Detect>"
  (cl:format cl:nil "string result~%float32 centerx~%float32 centery~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Yolov5Detect)))
  "Returns full string definition for message of type 'Yolov5Detect"
  (cl:format cl:nil "string result~%float32 centerx~%float32 centery~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Yolov5Detect>))
  (cl:+ 0
     4 (cl:length (cl:slot-value msg 'result))
     4
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Yolov5Detect>))
  "Converts a ROS message object to a list"
  (cl:list 'Yolov5Detect
    (cl:cons ':result (result msg))
    (cl:cons ':centerx (centerx msg))
    (cl:cons ':centery (centery msg))
))
