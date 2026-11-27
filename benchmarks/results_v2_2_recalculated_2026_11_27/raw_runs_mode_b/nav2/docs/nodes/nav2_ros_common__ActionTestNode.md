# Node Specification: `action_test_node`

- **Stable Unique ID**: `nav2_ros_common::ActionTestNode`
- **Fully Qualified Name**: `action_test_node`
- **Class / Executable**: `ActionTestNode`
- **Package**: `nav2_ros_common`
- **Namespace**: `/`
- **Source File**: `nav2_ros_common/test/test_actions.cpp`
- **Architectural Classification**: `test`
- **Is Test Entity**: `True`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_ros_common/test/test_actions.cpp` | `L219` | `node_definition` | `cpp_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `deactivate_server` | `std_msgs/msg/Empty` | `MessageType.UNKNOWN` | `default` | `test_actions.cpp:232` |
| `activate_server` | `std_msgs/msg/Empty` | `MessageType.UNKNOWN` | `default` | `test_actions.cpp:233` |
| `omit_preemption` | `std_msgs/msg/Empty` | `MessageType.UNKNOWN` | `default` | `test_actions.cpp:234` |
| `reject_goal` | `std_msgs/msg/Empty` | `MessageType.UNKNOWN` | `default` | `test_actions.cpp:235` |
| `allow_goal` | `std_msgs/msg/Empty` | `MessageType.UNKNOWN` | `default` | `test_actions.cpp:236` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `deactivate_server` | `std_msgs/msg/Empty` | `MessageType.UNKNOWN` | `default` | `test_actions.cpp:50` |
| `activate_server` | `std_msgs/msg/Empty` | `MessageType.UNKNOWN` | `default` | `test_actions.cpp:58` |
| `omit_preemption` | `std_msgs/msg/Empty` | `MessageType.UNKNOWN` | `default` | `test_actions.cpp:66` |
| `reject_goal` | `std_msgs/msg/Empty` | `MessageType.UNKNOWN` | `default` | `test_actions.cpp:74` |
| `allow_goal` | `std_msgs/msg/Empty` | `MessageType.UNKNOWN` | `default` | `test_actions.cpp:82` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `fibonacci` | `test_msgs/action/Fibonacci` | `client` | `test_actions.cpp:229` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*