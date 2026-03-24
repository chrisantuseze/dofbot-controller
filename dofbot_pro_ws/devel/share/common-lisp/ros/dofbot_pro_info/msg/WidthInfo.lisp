; Auto-generated. Do not edit!


(cl:in-package dofbot_pro_info-msg)


;//! \htmlinclude WidthInfo.msg.html

(cl:defclass <WidthInfo> (roslisp-msg-protocol:ros-message)
  ((L_x
    :reader L_x
    :initarg :L_x
    :type cl:float
    :initform 0.0)
   (L_y
    :reader L_y
    :initarg :L_y
    :type cl:float
    :initform 0.0)
   (R_x
    :reader R_x
    :initarg :R_x
    :type cl:float
    :initform 0.0)
   (R_y
    :reader R_y
    :initarg :R_y
    :type cl:float
    :initform 0.0))
)

(cl:defclass WidthInfo (<WidthInfo>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <WidthInfo>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'WidthInfo)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name dofbot_pro_info-msg:<WidthInfo> is deprecated: use dofbot_pro_info-msg:WidthInfo instead.")))

(cl:ensure-generic-function 'L_x-val :lambda-list '(m))
(cl:defmethod L_x-val ((m <WidthInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader dofbot_pro_info-msg:L_x-val is deprecated.  Use dofbot_pro_info-msg:L_x instead.")
  (L_x m))

(cl:ensure-generic-function 'L_y-val :lambda-list '(m))
(cl:defmethod L_y-val ((m <WidthInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader dofbot_pro_info-msg:L_y-val is deprecated.  Use dofbot_pro_info-msg:L_y instead.")
  (L_y m))

(cl:ensure-generic-function 'R_x-val :lambda-list '(m))
(cl:defmethod R_x-val ((m <WidthInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader dofbot_pro_info-msg:R_x-val is deprecated.  Use dofbot_pro_info-msg:R_x instead.")
  (R_x m))

(cl:ensure-generic-function 'R_y-val :lambda-list '(m))
(cl:defmethod R_y-val ((m <WidthInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader dofbot_pro_info-msg:R_y-val is deprecated.  Use dofbot_pro_info-msg:R_y instead.")
  (R_y m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <WidthInfo>) ostream)
  "Serializes a message object of type '<WidthInfo>"
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'L_x))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'L_y))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'R_x))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'R_y))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <WidthInfo>) istream)
  "Deserializes a message object of type '<WidthInfo>"
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'L_x) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'L_y) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'R_x) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'R_y) (roslisp-utils:decode-single-float-bits bits)))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<WidthInfo>)))
  "Returns string type for a message object of type '<WidthInfo>"
  "dofbot_pro_info/WidthInfo")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'WidthInfo)))
  "Returns string type for a message object of type 'WidthInfo"
  "dofbot_pro_info/WidthInfo")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<WidthInfo>)))
  "Returns md5sum for a message object of type '<WidthInfo>"
  "de9e03608448f2f1799b1dfee66084ae")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'WidthInfo)))
  "Returns md5sum for a message object of type 'WidthInfo"
  "de9e03608448f2f1799b1dfee66084ae")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<WidthInfo>)))
  "Returns full string definition for message of type '<WidthInfo>"
  (cl:format cl:nil "float32 L_x~%float32 L_y~%float32 R_x~%float32 R_y~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'WidthInfo)))
  "Returns full string definition for message of type 'WidthInfo"
  (cl:format cl:nil "float32 L_x~%float32 L_y~%float32 R_x~%float32 R_y~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <WidthInfo>))
  (cl:+ 0
     4
     4
     4
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <WidthInfo>))
  "Converts a ROS message object to a list"
  (cl:list 'WidthInfo
    (cl:cons ':L_x (L_x msg))
    (cl:cons ':L_y (L_y msg))
    (cl:cons ':R_x (R_x msg))
    (cl:cons ':R_y (R_y msg))
))
