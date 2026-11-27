# Node Specification: `nav2_rviz_selector_node`

- **Stable Unique ID**: `nav2_rviz_plugins::Nav2RvizSelectorNode`
- **Fully Qualified Name**: `nav2_rviz_plugins/nav2_rviz_selector_node`
- **Class / Executable**: `Nav2RvizSelectorNode`
- **Package**: `nav2_rviz_plugins`
- **Namespace**: `nav2_rviz_plugins`
- **Source File**: `nav2_rviz_plugins/src/selector.cpp`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_rviz_plugins/src/selector.cpp` | `L26` | `node_definition` | `cpp_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `controller_selector` | `std_msgs/msg/String` | `MessageType.UNKNOWN` | `default` | `selector.cpp:31` |
| `planner_selector` | `std_msgs/msg/String` | `MessageType.UNKNOWN` | `default` | `selector.cpp:32` |
| `goal_checker_selector` | `std_msgs/msg/String` | `MessageType.UNKNOWN` | `default` | `selector.cpp:34` |
| `smoother_selector` | `std_msgs/msg/String` | `MessageType.UNKNOWN` | `default` | `selector.cpp:35` |
| `progress_checker_selector` | `std_msgs/msg/String` | `MessageType.UNKNOWN` | `default` | `selector.cpp:37` |
| `path_handler_selector` | `std_msgs/msg/String` | `MessageType.UNKNOWN` | `default` | `selector.cpp:39` |

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*