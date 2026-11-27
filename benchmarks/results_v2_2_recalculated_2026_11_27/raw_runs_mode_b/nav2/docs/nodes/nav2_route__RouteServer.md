# Node Specification: `route_server`

- **Stable Unique ID**: `nav2_route::RouteServer`
- **Fully Qualified Name**: `nav2_route/route_server`
- **Class / Executable**: `nav2_route::RouteServer`
- **Package**: `nav2_route`
- **Namespace**: `nav2_route`
- **Source File**: `nav2_route/src/route_server.cpp`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_route/include/nav2_route/route_server.hpp` | `L54` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_route/src/route_server.cpp` | `L23` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_route/src/route_server.cpp` | `L412` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L78` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L84` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `route_graph` | `visualization_msgs/msg/MarkerArray` | `MessageType.UNKNOWN` | `default` | `route_server.cpp:37` |
| `route` | `nav2_msgs/msg/Route` | `MessageType.UNKNOWN` | `default` | `route_server.cpp:40` |

## Subscribers

*No subscribers declared.*

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `route_server/set_route_graph` | `nav2_msgs/srv/SetRouteGraph` | `server` | `route_server.cpp:52` |

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `compute_route` | `unknown/action/ComputeRoute` | `server` | `route_server.cpp:42` |
| `compute_and_track_route` | `unknown/action/ComputeAndTrackRoute` | `server` | `route_server.cpp:47` |

## Parameters

*No parameters declared.*