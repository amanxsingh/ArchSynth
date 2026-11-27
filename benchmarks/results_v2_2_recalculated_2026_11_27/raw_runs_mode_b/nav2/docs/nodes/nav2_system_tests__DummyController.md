# Node Specification: `DummyController`

- **Stable Unique ID**: `nav2_system_tests::DummyController`
- **Fully Qualified Name**: `nav2_system_tests/DummyController`
- **Class / Executable**: `nav2_system_tests::DummyController`
- **Package**: `nav2_system_tests`
- **Namespace**: `nav2_system_tests`
- **Source File**: `nav2_system_tests/src/dummy_controller/dummy_controller.cpp`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/dummy_controller/dummy_controller.hpp` | `L26` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_system_tests/src/dummy_controller/dummy_controller.cpp` | `L28` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `src/dummy_controller/CMakeLists.txt` | `L1` | `cmake_target` | `build_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `cmd_vel` | `geometry_msgs/msg/Twist` | `MessageType.UNKNOWN` | `default` | `dummy_controller.cpp:36` |

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*