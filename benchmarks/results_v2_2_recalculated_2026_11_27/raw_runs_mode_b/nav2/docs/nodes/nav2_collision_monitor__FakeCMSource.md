# Node Specification: `fake_cm_bag_source`

- **Stable Unique ID**: `nav2_collision_monitor::FakeCMSource`
- **Fully Qualified Name**: `fake_cm_bag_source`
- **Class / Executable**: `FakeCMSource`
- **Package**: `nav2_collision_monitor`
- **Namespace**: `/`
- **Source File**: `nav2_collision_monitor/test/bags/cm_moving_obstacle/fake_cm_bag_source.py`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_collision_monitor/test/bags/cm_moving_obstacle/fake_cm_bag_source.py` | `L39–L104` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `/clock` | `ClockMsg` | `MessageType.UNKNOWN` | `10` | `fake_cm_bag_source.py:45` |
| `/local_costmap/costmap` | `Costmap` | `MessageType.UNKNOWN` | `10` | `fake_cm_bag_source.py:46` |
| `/cmd_vel_smoothed` | `Twist` | `MessageType.UNKNOWN` | `10` | `fake_cm_bag_source.py:48` |

## Subscribers

*No subscribers declared.*

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*