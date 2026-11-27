# Node Specification: `JSPGUI_Controller`

- **Stable Unique ID**: `jaco2_controller::JSPGUIController`
- **Fully Qualified Name**: `JSPGUI_Controller`
- **Class / Executable**: `JSPGUIController`
- **Package**: `jaco2_controller`
- **Namespace**: `/`
- **Source File**: `jaco2_controller/jaco2_controller/jsp_gui_controller.py`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `jaco2_controller/jaco2_controller/jsp_gui_controller.py` | `L9–L47` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `arm_controller/joint_trajectory` | `JointTrajectory` | `MessageType.UNKNOWN` | `10` | `jsp_gui_controller.py:17` |
| `gripper_controller/joint_trajectory` | `JointTrajectory` | `MessageType.UNKNOWN` | `10` | `jsp_gui_controller.py:18` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `joint_commands` | `JointState` | `MessageType.UNKNOWN` | `10` | `jsp_gui_controller.py:19` |

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*