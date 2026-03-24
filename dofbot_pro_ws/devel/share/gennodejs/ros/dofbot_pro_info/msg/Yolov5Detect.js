// Auto-generated. Do not edit!

// (in-package dofbot_pro_info.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;

//-----------------------------------------------------------

class Yolov5Detect {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.result = null;
      this.centerx = null;
      this.centery = null;
    }
    else {
      if (initObj.hasOwnProperty('result')) {
        this.result = initObj.result
      }
      else {
        this.result = '';
      }
      if (initObj.hasOwnProperty('centerx')) {
        this.centerx = initObj.centerx
      }
      else {
        this.centerx = 0.0;
      }
      if (initObj.hasOwnProperty('centery')) {
        this.centery = initObj.centery
      }
      else {
        this.centery = 0.0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type Yolov5Detect
    // Serialize message field [result]
    bufferOffset = _serializer.string(obj.result, buffer, bufferOffset);
    // Serialize message field [centerx]
    bufferOffset = _serializer.float32(obj.centerx, buffer, bufferOffset);
    // Serialize message field [centery]
    bufferOffset = _serializer.float32(obj.centery, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type Yolov5Detect
    let len;
    let data = new Yolov5Detect(null);
    // Deserialize message field [result]
    data.result = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [centerx]
    data.centerx = _deserializer.float32(buffer, bufferOffset);
    // Deserialize message field [centery]
    data.centery = _deserializer.float32(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.result);
    return length + 12;
  }

  static datatype() {
    // Returns string type for a message object
    return 'dofbot_pro_info/Yolov5Detect';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'f6fde05b13d0b4d8a4f931c44fa3dda6';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    string result
    float32 centerx
    float32 centery
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new Yolov5Detect(null);
    if (msg.result !== undefined) {
      resolved.result = msg.result;
    }
    else {
      resolved.result = ''
    }

    if (msg.centerx !== undefined) {
      resolved.centerx = msg.centerx;
    }
    else {
      resolved.centerx = 0.0
    }

    if (msg.centery !== undefined) {
      resolved.centery = msg.centery;
    }
    else {
      resolved.centery = 0.0
    }

    return resolved;
    }
};

module.exports = Yolov5Detect;
