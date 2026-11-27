# Node Specification: `servo_keyboard_input`

- **Stable Unique ID**: `jaco2_servo::KeyboardServo`
- **Fully Qualified Name**: `servo_keyboard_input`
- **Class / Executable**: `KeyboardServo`
- **Package**: `jaco2_servo`
- **Namespace**: `/`
- **Source File**: `jaco2_servo/jaco2_servo/keyboard_teleop.py`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `jaco2_servo/jaco2_servo/keyboard_teleop.py` | `L88–L210` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `/servo_node/delta_joint_cmds` | `JointJog` | `MessageType.UNKNOWN` | `10` | `keyboard_teleop.py:94` |
| `/servo_node/delta_twist_cmds` | `TwistStamped` | `MessageType.UNKNOWN` | `10` | `keyboard_teleop.py:95` |

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*