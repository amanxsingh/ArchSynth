# Node Specification: `lifecycle_manager`

- **Stable Unique ID**: `nav2_lifecycle_manager::LifecycleManager`
- **Fully Qualified Name**: `nav2_lifecycle_manager/lifecycle_manager`
- **Class / Executable**: `nav2_lifecycle_manager::LifecycleManager`
- **Package**: `nav2_lifecycle_manager`
- **Namespace**: `nav2_lifecycle_manager`
- **Source File**: `nav2_lifecycle_manager/src/lifecycle_manager.cpp`
- **Architectural Classification**: `infrastructure`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_lifecycle_manager/include/nav2_lifecycle_manager/lifecycle_manager.hpp` | `L62` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_lifecycle_manager/src/lifecycle_manager.cpp` | `L36` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_lifecycle_manager/src/lifecycle_manager.cpp` | `L632` | `component_registration` | `cpp_ast_analyzer` | 1.0 |
| `CMakeLists.txt` | `L47` | `cmake_target` | `build_analyzer` | 1.0 |
| `CMakeLists.txt` | `L61` | `component_registration` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `lifecycle_manager/managed_nodes_activated` | `std_msgs/msg/Bool` | `MessageType.UNKNOWN` | `default` | `lifecycle_manager.cpp:237` |

## Subscribers

*No subscribers declared.*

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `lifecycle_manager/manage_nodes` | `unknown/srv/ManageLifecycleNodes` | `server` | `lifecycle_manager.cpp:219` |
| `lifecycle_manager/is_active` | `std_srvs/srv/Trigger` | `server` | `lifecycle_manager.cpp:225` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*