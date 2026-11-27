# Node Specification: `docking_server`

- **Stable Unique ID**: `opennav_docking::DockingServer`
- **Fully Qualified Name**: `opennav_docking/docking_server`
- **Class / Executable**: `opennav_docking::DockingServer`
- **Package**: `opennav_docking`
- **Namespace**: `opennav_docking`
- **Source File**: `nav2_docking/opennav_docking/src/docking_server.cpp`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_docking/opennav_docking/include/opennav_docking/docking_server.hpp` | `L46` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_docking/opennav_docking/src/docking_server.cpp` | `L28` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_docking/opennav_docking/src/docking_server.cpp` | `L803` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L101` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L114` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `cmd_vel` | `geometry_msgs/msg/TwistStamped` | `MessageType.UNKNOWN` | `default` | `docking_server.cpp:43` |

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `dock_robot` | `unknown/action/DockRobot` | `server` | `docking_server.cpp:51` |
| `undock_robot` | `unknown/action/UndockRobot` | `server` | `docking_server.cpp:57` |

## Parameters

*No parameters declared.*