# Node Specification: `waypoint_follower`

- **Stable Unique ID**: `nav2_waypoint_follower::WaypointFollower`
- **Fully Qualified Name**: `nav2_waypoint_follower/waypoint_follower`
- **Class / Executable**: `nav2_waypoint_follower::WaypointFollower`
- **Package**: `nav2_waypoint_follower`
- **Namespace**: `nav2_waypoint_follower`
- **Source File**: `nav2_waypoint_follower/src/waypoint_follower.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_waypoint_follower/include/nav2_waypoint_follower/waypoint_follower.hpp` | `L67` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_waypoint_follower/src/waypoint_follower.cpp` | `L32` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_waypoint_follower/src/waypoint_follower.cpp` | `L509` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L73` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L142` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

*No publishers declared.*

## Subscribers

*No subscribers declared.*

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `/fromLL` | `robot_localization/srv/FromLL` | `client` | `waypoint_follower.cpp:71` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `follow_waypoints` | `unknown/action/ActionT` | `server` | `waypoint_follower.cpp:63` |
| `follow_gps_waypoints` | `unknown/action/ActionTGPS` | `server` | `waypoint_follower.cpp:75` |

## Parameters

*No parameters declared.*