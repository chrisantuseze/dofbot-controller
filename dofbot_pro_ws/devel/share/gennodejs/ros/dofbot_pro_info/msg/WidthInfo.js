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

class WidthInfo {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.L_x = null;
      this.L_y = null;
      this.R_x = null;
      this.R_y = null;
    }
    else {
      if (initObj.hasOwnProperty('L_x')) {
        this.L_x = initObj.L_x
      }
      else {
        this.L_x = 0.0;
      }
      if (initObj.hasOwnProperty('L_y')) {
        this.L_y = initObj.L_y
      }
      else {
        this.L_y = 0.0;
      }
      if (initObj.hasOwnProperty('R_x')) {
        this.R_x = initObj.R_x
      }
      else {
        this.R_x = 0.0;
      }
      if (initObj.hasOwnProperty('R_y')) {
        this.R_y = initObj.R_y
      }
      else {
        this.R_y = 0.0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type WidthInfo
    // Serialize message field [L_x]
    bufferOffset = _serializer.float32(obj.L_x, buffer, bufferOffset);
    // Serialize message field [L_y]
    bufferOffset = _serializer.float32(obj.L_y, buffer, bufferOffset);
    // Serialize message field [R_x]
    bufferOffset = _serializer.float32(obj.R_x, buffer, bufferOffset);
    // Serialize message field [R_y]
    bufferOffset = _serializer.float32(obj.R_y, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type WidthInfo
    let len;
    let data = new WidthInfo(null);
    // Deserialize message field [L_x]
    data.L_x = _deserializer.float32(buffer, bufferOffset);
    // Deserialize message field [L_y]
    data.L_y = _deserializer.float32(buffer, bufferOffset);
    // Deserialize message field [R_x]
    data.R_x = _deserializer.float32(buffer, bufferOffset);
    // Deserialize message field [R_y]
    data.R_y = _deserializer.float32(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    return 16;
  }

  static datatype() {
    // Returns string type for a message object
    return 'dofbot_pro_info/WidthInfo';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'de9e03608448f2f1799b1dfee66084ae';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    float32 L_x
    float32 L_y
    float32 R_x
    float32 R_y
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new WidthInfo(null);
    if (msg.L_x !== undefined) {
      resolved.L_x = msg.L_x;
    }
    else {
      resolved.L_x = 0.0
    }

    if (msg.L_y !== undefined) {
      resolved.L_y = msg.L_y;
    }
    else {
      resolved.L_y = 0.0
    }

    if (msg.R_x !== undefined) {
      resolved.R_x = msg.R_x;
    }
    else {
      resolved.R_x = 0.0
    }

    if (msg.R_y !== undefined) {
      resolved.R_y = msg.R_y;
    }
    else {
      resolved.R_y = 0.0
    }

    return resolved;
    }
};

module.exports = WidthInfo;
