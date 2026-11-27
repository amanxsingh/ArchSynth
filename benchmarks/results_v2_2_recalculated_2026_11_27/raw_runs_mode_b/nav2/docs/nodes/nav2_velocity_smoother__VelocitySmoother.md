# Node Specification: `velocity_smoother`

- **Stable Unique ID**: `nav2_velocity_smoother::VelocitySmoother`
- **Fully Qualified Name**: `nav2_velocity_smoother/velocity_smoother`
- **Class / Executable**: `nav2_velocity_smoother::VelocitySmoother`
- **Package**: `nav2_velocity_smoother`
- **Namespace**: `nav2_velocity_smoother`
- **Source File**: `nav2_velocity_smoother/src/velocity_smoother.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_velocity_smoother/include/nav2_velocity_smoother/velocity_smoother.hpp` | `L41` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_velocity_smoother/src/velocity_smoother.cpp` | `L31` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_velocity_smoother/src/velocity_smoother.cpp` | `L636` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L40` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L45` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `cmd_vel_smoothed` | `geometry_msgs/msg/TwistStamped` | `MessageType.UNKNOWN` | `default` | `velocity_smoother.cpp:143` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `cmd_vel` | `geometry_msgs/msg/TwistStamped` | `MessageType.UNKNOWN` | `default` | `velocity_smoother.cpp:144` |

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*