# Node Specification: `test_collision_checker`

- **Stable Unique ID**: `opennav_docking::TestCollisionChecker`
- **Fully Qualified Name**: `opennav_docking/test_collision_checker`
- **Class / Executable**: `opennav_docking::TestCollisionChecker`
- **Package**: `opennav_docking`
- **Namespace**: `opennav_docking`
- **Source File**: `nav2_docking/opennav_docking/test/test_controller.cpp`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_docking/opennav_docking/test/test_controller.cpp` | `L57` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L101` | `cmake_target` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `test_footprint` | `geometry_msgs/msg/PolygonStamped` | `MessageType.UNKNOWN` | `default` | `test_controller.cpp:77` |

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*