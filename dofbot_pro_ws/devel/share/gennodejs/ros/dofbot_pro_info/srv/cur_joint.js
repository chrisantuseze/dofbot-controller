// Auto-generated. Do not edit!

// (in-package dofbot_pro_info.srv)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;

//-----------------------------------------------------------


//-----------------------------------------------------------

class cur_jointRequest {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.srv_joints = null;
    }
    else {
      if (initObj.hasOwnProperty('srv_joints')) {
        this.srv_joints = initObj.srv_joints
      }
      else {
        this.srv_joints = '';
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type cur_jointRequest
    // Serialize message field [srv_joints]
    bufferOffset = _serializer.string(obj.srv_joints, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type cur_jointRequest
    let len;
    let data = new cur_jointRequest(null);
    // Deserialize message field [srv_joints]
    data.srv_joints = _deserializer.string(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.srv_joints);
    return length + 4;
  }

  static datatype() {
    // Returns string type for a service object
    return 'dofbot_pro_info/cur_jointRequest';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '316e22b41dfc06dd91c3544d4b9ba5ed';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    # request
    string  srv_joints
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new cur_jointRequest(null);
    if (msg.srv_joints !== undefined) {
      resolved.srv_joints = msg.srv_joints;
    }
    else {
      resolved.srv_joints = ''
    }

    return resolved;
    }
};

class cur_jointResponse {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.srv_joint1 = null;
      this.srv_joint2 = null;
      this.srv_joint3 = null;
      this.srv_joint4 = null;
      this.srv_joint5 = null;
      this.srv_joint6 = null;
    }
    else {
      if (initObj.hasOwnProperty('srv_joint1')) {
        this.srv_joint1 = initObj.srv_joint1
      }
      else {
        this.srv_joint1 = 0.0;
      }
      if (initObj.hasOwnProperty('srv_joint2')) {
        this.srv_joint2 = initObj.srv_joint2
      }
      else {
        this.srv_joint2 = 0.0;
      }
      if (initObj.hasOwnProperty('srv_joint3')) {
        this.srv_joint3 = initObj.srv_joint3
      }
      else {
        this.srv_joint3 = 0.0;
      }
      if (initObj.hasOwnProperty('srv_joint4')) {
        this.srv_joint4 = initObj.srv_joint4
      }
      else {
        this.srv_joint4 = 0.0;
      }
      if (initObj.hasOwnProperty('srv_joint5')) {
        this.srv_joint5 = initObj.srv_joint5
      }
      else {
        this.srv_joint5 = 0.0;
      }
      if (initObj.hasOwnProperty('srv_joint6')) {
        this.srv_joint6 = initObj.srv_joint6
      }
      else {
        this.srv_joint6 = 0.0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type cur_jointResponse
    // Serialize message field [srv_joint1]
    bufferOffset = _serializer.float64(obj.srv_joint1, buffer, bufferOffset);
    // Serialize message field [srv_joint2]
    bufferOffset = _serializer.float64(obj.srv_joint2, buffer, bufferOffset);
    // Serialize message field [srv_joint3]
    bufferOffset = _serializer.float64(obj.srv_joint3, buffer, bufferOffset);
    // Serialize message field [srv_joint4]
    bufferOffset = _serializer.float64(obj.srv_joint4, buffer, bufferOffset);
    // Serialize message field [srv_joint5]
    bufferOffset = _serializer.float64(obj.srv_joint5, buffer, bufferOffset);
    // Serialize message field [srv_joint6]
    bufferOffset = _serializer.float64(obj.srv_joint6, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type cur_jointResponse
    let len;
    let data = new cur_jointResponse(null);
    // Deserialize message field [srv_joint1]
    data.srv_joint1 = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [srv_joint2]
    data.srv_joint2 = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [srv_joint3]
    data.srv_joint3 = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [srv_joint4]
    data.srv_joint4 = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [srv_joint5]
    data.srv_joint5 = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [srv_joint6]
    data.srv_joint6 = _deserializer.float64(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    return 48;
  }

  static datatype() {
    // Returns string type for a service object
    return 'dofbot_pro_info/cur_jointResponse';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '2a8aa04b9b18701c3796ea044e492219';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    # response
    float64 srv_joint1
    float64 srv_joint2
    float64 srv_joint3
    float64 srv_joint4
    float64 srv_joint5
    float64 srv_joint6
    
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new cur_jointResponse(null);
    if (msg.srv_joint1 !== undefined) {
      resolved.srv_joint1 = msg.srv_joint1;
    }
    else {
      resolved.srv_joint1 = 0.0
    }

    if (msg.srv_joint2 !== undefined) {
      resolved.srv_joint2 = msg.srv_joint2;
    }
    else {
      resolved.srv_joint2 = 0.0
    }

    if (msg.srv_joint3 !== undefined) {
      resolved.srv_joint3 = msg.srv_joint3;
    }
    else {
      resolved.srv_joint3 = 0.0
    }

    if (msg.srv_joint4 !== undefined) {
      resolved.srv_joint4 = msg.srv_joint4;
    }
    else {
      resolved.srv_joint4 = 0.0
    }

    if (msg.srv_joint5 !== undefined) {
      resolved.srv_joint5 = msg.srv_joint5;
    }
    else {
      resolved.srv_joint5 = 0.0
    }

    if (msg.srv_joint6 !== undefined) {
      resolved.srv_joint6 = msg.srv_joint6;
    }
    else {
      resolved.srv_joint6 = 0.0
    }

    return resolved;
    }
};

module.exports = {
  Request: cur_jointRequest,
  Response: cur_jointResponse,
  md5sum() { return '7bf4e10c269e4b461f9707a22ed78be1'; },
  datatype() { return 'dofbot_pro_info/cur_joint'; }
};
