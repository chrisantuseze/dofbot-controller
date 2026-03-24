; Auto-generated. Do not edit!


(cl:in-package dofbot_pro_info-srv)


;//! \htmlinclude cur_joint-request.msg.html

(cl:defclass <cur_joint-request> (roslisp-msg-protocol:ros-message)
  ((srv_joints
    :reader srv_joints
    :initarg :srv_joints
    :type cl:string
    :initform ""))
)

(cl:defclass cur_joint-request (<cur_joint-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <cur_joint-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'cur_joint-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name dofbot_pro_info-srv:<cur_joint-request> is deprecated: use dofbot_pro_info-srv:cur_joint-request instead.")))

(cl:ensure-generic-function 'srv_joints-val :lambda-list '(m))
(cl:defmethod srv_joints-val ((m <cur_joint-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader dofbot_pro_info-srv:srv_joints-val is deprecated.  Use dofbot_pro_info-srv:srv_joints instead.")
  (srv_joints m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <cur_joint-request>) ostream)
  "Serializes a message object of type '<cur_joint-request>"
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'srv_joints))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'srv_joints))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <cur_joint-request>) istream)
  "Deserializes a message object of type '<cur_joint-request>"
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'srv_joints) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'srv_joints) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<cur_joint-request>)))
  "Returns string type for a service object of type '<cur_joint-request>"
  "dofbot_pro_info/cur_jointRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'cur_joint-request)))
  "Returns string type for a service object of type 'cur_joint-request"
  "dofbot_pro_info/cur_jointRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<cur_joint-request>)))
  "Returns md5sum for a message object of type '<cur_joint-request>"
  "7bf4e10c269e4b461f9707a22ed78be1")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'cur_joint-request)))
  "Returns md5sum for a message object of type 'cur_joint-request"
  "7bf4e10c269e4b461f9707a22ed78be1")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<cur_joint-request>)))
  "Returns full string definition for message of type '<cur_joint-request>"
  (cl:format cl:nil "# request~%string  srv_joints~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'cur_joint-request)))
  "Returns full string definition for message of type 'cur_joint-request"
  (cl:format cl:nil "# request~%string  srv_joints~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <cur_joint-request>))
  (cl:+ 0
     4 (cl:length (cl:slot-value msg 'srv_joints))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <cur_joint-request>))
  "Converts a ROS message object to a list"
  (cl:list 'cur_joint-request
    (cl:cons ':srv_joints (srv_joints msg))
))
;//! \htmlinclude cur_joint-response.msg.html

(cl:defclass <cur_joint-response> (roslisp-msg-protocol:ros-message)
  ((srv_joint1
    :reader srv_joint1
    :initarg :srv_joint1
    :type cl:float
    :initform 0.0)
   (srv_joint2
    :reader srv_joint2
    :initarg :srv_joint2
    :type cl:float
    :initform 0.0)
   (srv_joint3
    :reader srv_joint3
    :initarg :srv_joint3
    :type cl:float
    :initform 0.0)
   (srv_joint4
    :reader srv_joint4
    :initarg :srv_joint4
    :type cl:float
    :initform 0.0)
   (srv_joint5
    :reader srv_joint5
    :initarg :srv_joint5
    :type cl:float
    :initform 0.0)
   (srv_joint6
    :reader srv_joint6
    :initarg :srv_joint6
    :type cl:float
    :initform 0.0))
)

(cl:defclass cur_joint-response (<cur_joint-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <cur_joint-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'cur_joint-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name dofbot_pro_info-srv:<cur_joint-response> is deprecated: use dofbot_pro_info-srv:cur_joint-response instead.")))

(cl:ensure-generic-function 'srv_joint1-val :lambda-list '(m))
(cl:defmethod srv_joint1-val ((m <cur_joint-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader dofbot_pro_info-srv:srv_joint1-val is deprecated.  Use dofbot_pro_info-srv:srv_joint1 instead.")
  (srv_joint1 m))

(cl:ensure-generic-function 'srv_joint2-val :lambda-list '(m))
(cl:defmethod srv_joint2-val ((m <cur_joint-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader dofbot_pro_info-srv:srv_joint2-val is deprecated.  Use dofbot_pro_info-srv:srv_joint2 instead.")
  (srv_joint2 m))

(cl:ensure-generic-function 'srv_joint3-val :lambda-list '(m))
(cl:defmethod srv_joint3-val ((m <cur_joint-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader dofbot_pro_info-srv:srv_joint3-val is deprecated.  Use dofbot_pro_info-srv:srv_joint3 instead.")
  (srv_joint3 m))

(cl:ensure-generic-function 'srv_joint4-val :lambda-list '(m))
(cl:defmethod srv_joint4-val ((m <cur_joint-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader dofbot_pro_info-srv:srv_joint4-val is deprecated.  Use dofbot_pro_info-srv:srv_joint4 instead.")
  (srv_joint4 m))

(cl:ensure-generic-function 'srv_joint5-val :lambda-list '(m))
(cl:defmethod srv_joint5-val ((m <cur_joint-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader dofbot_pro_info-srv:srv_joint5-val is deprecated.  Use dofbot_pro_info-srv:srv_joint5 instead.")
  (srv_joint5 m))

(cl:ensure-generic-function 'srv_joint6-val :lambda-list '(m))
(cl:defmethod srv_joint6-val ((m <cur_joint-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader dofbot_pro_info-srv:srv_joint6-val is deprecated.  Use dofbot_pro_info-srv:srv_joint6 instead.")
  (srv_joint6 m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <cur_joint-response>) ostream)
  "Serializes a message object of type '<cur_joint-response>"
  (cl:let ((bits (roslisp-utils:encode-double-float-bits (cl:slot-value msg 'srv_joint1))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 32) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 40) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 48) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 56) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-double-float-bits (cl:slot-value msg 'srv_joint2))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 32) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 40) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 48) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 56) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-double-float-bits (cl:slot-value msg 'srv_joint3))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 32) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 40) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 48) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 56) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-double-float-bits (cl:slot-value msg 'srv_joint4))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 32) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 40) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 48) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 56) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-double-float-bits (cl:slot-value msg 'srv_joint5))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 32) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 40) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 48) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 56) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-double-float-bits (cl:slot-value msg 'srv_joint6))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 32) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 40) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 48) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 56) bits) ostream))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <cur_joint-response>) istream)
  "Deserializes a message object of type '<cur_joint-response>"
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 32) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 40) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 48) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 56) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'srv_joint1) (roslisp-utils:decode-double-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 32) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 40) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 48) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 56) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'srv_joint2) (roslisp-utils:decode-double-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 32) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 40) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 48) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 56) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'srv_joint3) (roslisp-utils:decode-double-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 32) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 40) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 48) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 56) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'srv_joint4) (roslisp-utils:decode-double-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 32) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 40) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 48) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 56) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'srv_joint5) (roslisp-utils:decode-double-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 32) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 40) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 48) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 56) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'srv_joint6) (roslisp-utils:decode-double-float-bits bits)))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<cur_joint-response>)))
  "Returns string type for a service object of type '<cur_joint-response>"
  "dofbot_pro_info/cur_jointResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'cur_joint-response)))
  "Returns string type for a service object of type 'cur_joint-response"
  "dofbot_pro_info/cur_jointResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<cur_joint-response>)))
  "Returns md5sum for a message object of type '<cur_joint-response>"
  "7bf4e10c269e4b461f9707a22ed78be1")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'cur_joint-response)))
  "Returns md5sum for a message object of type 'cur_joint-response"
  "7bf4e10c269e4b461f9707a22ed78be1")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<cur_joint-response>)))
  "Returns full string definition for message of type '<cur_joint-response>"
  (cl:format cl:nil "# response~%float64 srv_joint1~%float64 srv_joint2~%float64 srv_joint3~%float64 srv_joint4~%float64 srv_joint5~%float64 srv_joint6~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'cur_joint-response)))
  "Returns full string definition for message of type 'cur_joint-response"
  (cl:format cl:nil "# response~%float64 srv_joint1~%float64 srv_joint2~%float64 srv_joint3~%float64 srv_joint4~%float64 srv_joint5~%float64 srv_joint6~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <cur_joint-response>))
  (cl:+ 0
     8
     8
     8
     8
     8
     8
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <cur_joint-response>))
  "Converts a ROS message object to a list"
  (cl:list 'cur_joint-response
    (cl:cons ':srv_joint1 (srv_joint1 msg))
    (cl:cons ':srv_joint2 (srv_joint2 msg))
    (cl:cons ':srv_joint3 (srv_joint3 msg))
    (cl:cons ':srv_joint4 (srv_joint4 msg))
    (cl:cons ':srv_joint5 (srv_joint5 msg))
    (cl:cons ':srv_joint6 (srv_joint6 msg))
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'cur_joint)))
  'cur_joint-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'cur_joint)))
  'cur_joint-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'cur_joint)))
  "Returns string type for a service object of type '<cur_joint>"
  "dofbot_pro_info/cur_joint")