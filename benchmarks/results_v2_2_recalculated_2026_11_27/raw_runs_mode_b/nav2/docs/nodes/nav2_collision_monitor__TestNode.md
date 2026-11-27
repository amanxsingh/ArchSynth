# Node Specification: `exclusion_zone_test_node`

- **Stable Unique ID**: `nav2_collision_monitor::TestNode`
- **Fully Qualified Name**: `exclusion_zone_test_node`
- **Class / Executable**: `TestNode`
- **Package**: `nav2_collision_monitor`
- **Namespace**: `/`
- **Source File**: `nav2_collision_monitor/test/exclusion_zone_test.cpp`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `True`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_collision_monitor/test/exclusion_zone_test.cpp` | `L147` | `node_definition` | `cpp_ast_analyzer` | 1.0 |

## Publishers

*No publishers declared.*

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `~/ZONE_NAME` | `geometry_msgs/msg/PolygonStamped` | `MessageType.UNKNOWN` | `default` | `exclusion_zone_test.cpp:790` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `~/" + std::string(SOURCE_NAME) + "/add_exclusion_zone` | `nav2_msgs/srv/AddExclusionZone` | `client` | `exclusion_zone_test.cpp:912` |
| `~/" + std::string(SOURCE_NAME) + "/remove_exclusion_zone` | `nav2_msgs/srv/RemoveExclusionZone` | `client` | `exclusion_zone_test.cpp:914` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*