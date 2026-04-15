import math

# ── Constants ─────────────────────────────────────────────────────────────────

NUM_JOINTS   = 6
RAD2DEG      = 180.0 / math.pi
DEG2RAD      = math.pi / 180.0

# Servo degree range for the gripper
GRIPPER_MIN_DEG       = 30.0
GRIPPER_MAX_DEG       = 180.0
# joint_states range for the gripper (after arm_driver normalisation)
GRIPPER_STATE_MIN_DEG = 0.0
GRIPPER_STATE_MAX_DEG = 90.0

JOINT_NAMES = [
    "Arm1_Joint", "Arm2_Joint", "Arm3_Joint",
    "Arm4_Joint", "Arm5_Joint", "grip_joint",
]

# ROS topic names
JOINT_STATE_TOPIC   = "joint_states"
IMAGE_TOPIC         = "/camera/color/image_raw"

# Publish to /policy/action so robot_controller.py on the Jetson can
# safety-check and sync motion before forwarding to arm_driver.py.
# Set to "TargetAngle" to bypass the controller (direct mode, no safety gate).
POLICY_ACTION_TOPIC = "/policy/action"

# robot_controller.py publishes True here when the arm has settled at its
# last target — used to synchronise inference rate with actual motion.
ROBOT_READY_TOPIC   = "/robot/ready"

# Episode control — publish "start"/"stop"/"home"/"reset" here
ROBOT_CMD_TOPIC     = "/robot/cmd"

JOINT_STATE_TYPE    = "sensor_msgs/JointState"
IMAGE_TYPE          = "sensor_msgs/Image"
ACTION_MSG_TYPE     = "dofbot_pro_info/ArmJoint"    # from yahboomcar_msgs
BOOL_TYPE           = "std_msgs/Bool"
STRING_TYPE         = "std_msgs/String"

