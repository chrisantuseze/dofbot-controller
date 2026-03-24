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

class pos_info {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.name = null;
      this.pos1 = null;
      this.pos2 = null;
      this.pos3 = null;
      this.Roll = null;
      this.Pitch = null;
      this.Yaw = null;
    }
    else {
      if (initObj.hasOwnProperty('name')) {
        this.name = initObj.name
      }
      else {
        this.name = '';
      }
      if (initObj.hasOwnProperty('pos1')) {
        this.pos1 = initObj.pos1
      }
      else {
        this.pos1 = 0.0;
      }
      if (initObj.hasOwnProperty('pos2')) {
        this.pos2 = initObj.pos2
      }
      else {
        this.pos2 = 0.0;
      }
      if (initObj.hasOwnProperty('pos3')) {
        this.pos3 = initObj.pos3
      }
      else {
        this.pos3 = 0.0;
      }
      if (initObj.hasOwnProperty('Roll')) {
        this.Roll = initObj.Roll
      }
      else {
        this.Roll = 0.0;
      }
      if (initObj.hasOwnProperty('Pitch')) {
        this.Pitch = initObj.Pitch
      }
      else {
        this.Pitch = 0.0;
      }
      if (initObj.hasOwnProperty('Yaw')) {
        this.Yaw = initObj.Yaw
      }
      else {
        this.Yaw = 0.0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type pos_info
    // Serialize message field [name]
    bufferOffset = _serializer.string(obj.name, buffer, bufferOffset);
    // Serialize message field [pos1]
    bufferOffset = _serializer.float64(obj.pos1, buffer, bufferOffset);
    // Serialize message field [pos2]
    bufferOffset = _serializer.float64(obj.pos2, buffer, bufferOffset);
    // Serialize message field [pos3]
    bufferOffset = _serializer.float64(obj.pos3, buffer, bufferOffset);
    // Serialize message field [Roll]
    bufferOffset = _serializer.float64(obj.Roll, buffer, bufferOffset);
    // Serialize message field [Pitch]
    bufferOffset = _serializer.float64(obj.Pitch, buffer, bufferOffset);
    // Serialize message field [Yaw]
    bufferOffset = _serializer.float64(obj.Yaw, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type pos_info
    let len;
    let data = new pos_info(null);
    // Deserialize message field [name]
    data.name = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [pos1]
    data.pos1 = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [pos2]
    data.pos2 = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [pos3]
    data.pos3 = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [Roll]
    data.Roll = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [Pitch]
    data.Pitch = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [Yaw]
    data.Yaw = _deserializer.float64(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.name);
    return length + 52;
  }

  static datatype() {
    // Returns string type for a message object
    return 'dofbot_pro_info/pos_info';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '464446b8e571013c21f5be23c938371e';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    string  name
    float64 pos1
    float64 pos2
    float64 pos3
    float64 Roll
    float64 Pitch
    float64 Yaw
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new pos_info(null);
    if (msg.name !== undefined) {
      resolved.name = msg.name;
    }
    else {
      resolved.name = ''
    }

    if (msg.pos1 !== undefined) {
      resolved.pos1 = msg.pos1;
    }
    else {
      resolved.pos1 = 0.0
    }

    if (msg.pos2 !== undefined) {
      resolved.pos2 = msg.pos2;
    }
    else {
      resolved.pos2 = 0.0
    }

    if (msg.pos3 !== undefined) {
      resolved.pos3 = msg.pos3;
    }
    else {
      resolved.pos3 = 0.0
    }

    if (msg.Roll !== undefined) {
      resolved.Roll = msg.Roll;
    }
    else {
      resolved.Roll = 0.0
    }

    if (msg.Pitch !== undefined) {
      resolved.Pitch = msg.Pitch;
    }
    else {
      resolved.Pitch = 0.0
    }

    if (msg.Yaw !== undefined) {
      resolved.Yaw = msg.Yaw;
    }
    else {
      resolved.Yaw = 0.0
    }

    return resolved;
    }
};

module.exports = pos_info;
