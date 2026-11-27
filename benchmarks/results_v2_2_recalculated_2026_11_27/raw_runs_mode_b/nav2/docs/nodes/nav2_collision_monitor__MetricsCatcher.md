# Node Specification: `cm_metrics_catcher`

- **Stable Unique ID**: `nav2_collision_monitor::MetricsCatcher`
- **Fully Qualified Name**: `cm_metrics_catcher`
- **Class / Executable**: `MetricsCatcher`
- **Package**: `nav2_collision_monitor`
- **Namespace**: `/`
- **Source File**: `nav2_collision_monitor/test/collision_monitor_node_bag.cpp`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_collision_monitor/test/collision_monitor_node_bag.cpp` | `L43` | `node_definition` | `cpp_ast_analyzer` | 1.0 |

## Publishers

*No publishers declared.*

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `/local_costmap/costmap` | `nav2_msgs/msg/Costmap` | `MessageType.UNKNOWN` | `default` | `collision_monitor_node_bag.cpp:75` |
| `/clock` | `rosgraph_msgs/msg/Clock` | `MessageType.UNKNOWN` | `default` | `collision_monitor_node_bag.cpp:81` |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | `MessageType.UNKNOWN` | `default` | `collision_monitor_node_bag.cpp:88` |
| `/collision_state` | `unknown/msg/CollisionMonitorState` | `MessageType.UNKNOWN` | `default` | `collision_monitor_node_bag.cpp:100` |

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*