
"use strict";

let Yolov5Detect = require('./Yolov5Detect.js');
let ArmJoint = require('./ArmJoint.js');
let Position = require('./Position.js');
let CenterXY = require('./CenterXY.js');
let pos_info = require('./pos_info.js');
let ShapeInfo = require('./ShapeInfo.js');
let WidthInfo = require('./WidthInfo.js');
let AprilTagInfo = require('./AprilTagInfo.js');
let joint_info = require('./joint_info.js');
let Image_Msg = require('./Image_Msg.js');

module.exports = {
  Yolov5Detect: Yolov5Detect,
  ArmJoint: ArmJoint,
  Position: Position,
  CenterXY: CenterXY,
  pos_info: pos_info,
  ShapeInfo: ShapeInfo,
  WidthInfo: WidthInfo,
  AprilTagInfo: AprilTagInfo,
  joint_info: joint_info,
  Image_Msg: Image_Msg,
};
