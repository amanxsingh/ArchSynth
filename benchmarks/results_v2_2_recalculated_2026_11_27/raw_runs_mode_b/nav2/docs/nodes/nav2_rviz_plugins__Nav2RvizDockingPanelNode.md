# Node Specification: `nav2_rviz_docking_panel_node`

- **Stable Unique ID**: `nav2_rviz_plugins::Nav2RvizDockingPanelNode`
- **Fully Qualified Name**: `nav2_rviz_plugins/nav2_rviz_docking_panel_node`
- **Class / Executable**: `Nav2RvizDockingPanelNode`
- **Package**: `nav2_rviz_plugins`
- **Namespace**: `nav2_rviz_plugins`
- **Source File**: `nav2_rviz_plugins/src/docking_panel.cpp`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `nav2_rviz_plugins/src/docking_panel.cpp` | `L172` | `node_definition` | `cpp_ast_analyzer` | 1.0 |

## Publishers

*No publishers declared.*

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `dock_robot/_action/feedback` | `Dock/Impl/FeedbackMessage` | `MessageType.UNKNOWN` | `default` | `docking_panel.cpp:286` |
| `dock_robot/_action/status` | `action_msgs/msg/GoalStatusArray` | `MessageType.UNKNOWN` | `default` | `docking_panel.cpp:294` |
| `undock_robot/_action/status` | `action_msgs/msg/GoalStatusArray` | `MessageType.UNKNOWN` | `default` | `docking_panel.cpp:306` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `client_node_` | `unknown/srv/Dock` | `client` | `docking_panel.cpp:235` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*