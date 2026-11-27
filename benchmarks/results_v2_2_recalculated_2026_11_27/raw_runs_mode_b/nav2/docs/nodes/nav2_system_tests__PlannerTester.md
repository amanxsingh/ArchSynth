# Node Specification: `PlannerTester`

- **Stable Unique ID**: `nav2_system_tests::PlannerTester`
- **Fully Qualified Name**: `nav2_system_tests/PlannerTester`
- **Class / Executable**: `nav2_system_tests::PlannerTester`
- **Package**: `nav2_system_tests`
- **Namespace**: `nav2_system_tests`
- **Source File**: `nav2_system_tests/src/planning/planner_tester.cpp`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_system_tests/src/planning/planner_tester.hpp` | `L131` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `nav2_system_tests/src/planning/planner_tester.cpp` | `L41` | `node_definition` | `cpp_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `map` | `nav_msgs/msg/OccupancyGrid` | `MessageType.UNKNOWN` | `default` | `planner_tester.cpp:78` |

## Subscribers

*No subscribers declared.*

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `is_path_valid` | `nav2_msgs/srv/IsPathValid` | `client` | `planner_tester.cpp:80` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*