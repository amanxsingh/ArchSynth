# Node Specification: `test_docking_server`

- **Stable Unique ID**: `opennav_docking::TestDockingServer`
- **Fully Qualified Name**: `test_docking_server`
- **Class / Executable**: `TestDockingServer`
- **Package**: `opennav_docking`
- **Namespace**: `/`
- **Source File**: `nav2_docking/opennav_docking/test/test_docking_server.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_docking/opennav_docking/test/test_docking_server.py` | `L128` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `odom` | `nav_msgs/msg/Odometry` | `MessageType.UNKNOWN` | `default` | `test_docking_server.py:132` |
| `battery_state` | `sensor_msgs/msg/BatteryState` | `MessageType.UNKNOWN` | `default` | `test_docking_server.py:250` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `cmd_vel` | `geometry_msgs/msg/TwistStamped` | `MessageType.UNKNOWN` | `default` | `test_docking_server.py:241` |

## Services

*No services declared.*

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `dock_robot` | `nav2_msgs/action/DockRobot` | `client` | `test_docking_server.py:236` |
| `undock_robot` | `nav2_msgs/action/UndockRobot` | `client` | `test_docking_server.py:238` |
| `navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | `server` | `test_docking_server.py:257` |

## Parameters

*No parameters declared.*