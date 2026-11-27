# Node Specification: `bt_navigator`

- **Stable Unique ID**: `nav2_bt_navigator::BtNavigator`
- **Fully Qualified Name**: `nav2_bt_navigator/bt_navigator`
- **Class / Executable**: `nav2_bt_navigator::BtNavigator`
- **Package**: `nav2_bt_navigator`
- **Namespace**: `nav2_bt_navigator`
- **Source File**: `nav2_bt_navigator/src/bt_navigator.cpp`
- **Architectural Classification**: `behavior`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_bt_navigator/include/nav2_bt_navigator/bt_navigator.hpp` | `L38` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_bt_navigator/src/bt_navigator.cpp` | `L35` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_bt_navigator/src/bt_navigator.cpp` | `L196` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L51` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L111` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

*No publishers declared.*

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

| Action Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | `server` | `bt_navigator.cpp:84` |
| `navigate_through_poses` | `nav2_msgs/action/NavigateThroughPoses` | `server` | `bt_navigator.cpp:84` |

## Parameters

*No parameters declared.*