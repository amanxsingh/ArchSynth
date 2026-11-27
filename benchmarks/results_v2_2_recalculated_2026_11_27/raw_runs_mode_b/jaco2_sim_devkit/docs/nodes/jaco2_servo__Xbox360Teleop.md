# Node Specification: `xbox360_teleop`

- **Stable Unique ID**: `jaco2_servo::Xbox360Teleop`
- **Fully Qualified Name**: `xbox360_teleop`
- **Class / Executable**: `Xbox360Teleop`
- **Package**: `jaco2_servo`
- **Namespace**: `/`
- **Source File**: `jaco2_servo/jaco2_servo/joystick_teleop.py`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `jaco2_servo/jaco2_servo/joystick_teleop.py` | `L43–L189` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `/servo_node/delta_joint_cmds` | `JointJog` | `MessageType.UNKNOWN` | `10` | `joystick_teleop.py:57` |
| `/servo_node/delta_twist_cmds` | `TwistStamped` | `MessageType.UNKNOWN` | `10` | `joystick_teleop.py:58` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `/joy` | `Joy` | `MessageType.UNKNOWN` | `self.joy_callback` | `joystick_teleop.py:63` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `/servo_node/start_servo` | `Trigger` | `client` | `joystick_teleop.py:59` |
| `/servo_node/stop_servo` | `Trigger` | `client` | `joystick_teleop.py:60` |
| `/servo_node/switch_command_type` | `ServoCommandType` | `client` | `joystick_teleop.py:61` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*