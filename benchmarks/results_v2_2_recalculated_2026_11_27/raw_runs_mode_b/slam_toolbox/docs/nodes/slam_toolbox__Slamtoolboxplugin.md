# Node Specification: `SlamToolboxPlugin`

- **Stable Unique ID**: `slam_toolbox::Slamtoolboxplugin`
- **Fully Qualified Name**: `slam_toolbox/SlamToolboxPlugin`
- **Class / Executable**: `Slamtoolboxplugin`
- **Package**: `slam_toolbox`
- **Namespace**: `slam_toolbox`
- **Source File**: `rviz_plugin/slam_toolbox_rviz_plugin.cpp`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `rviz_plugin/slam_toolbox_rviz_plugin.cpp` | `L48` | `node_definition` | `cpp_ast_analyzer` | 1.0 |

## Publishers

*No publishers declared.*

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `initialpose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | `MessageType.UNKNOWN` | `default` | `slam_toolbox_rviz_plugin.cpp:59` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `slam_toolbox/serialize_map` | `slam_toolbox/srv/SerializePoseGraph` | `client` | `slam_toolbox_rviz_plugin.cpp:64` |
| `slam_toolbox/deserialize_map` | `slam_toolbox/srv/DeserializePoseGraph` | `client` | `slam_toolbox_rviz_plugin.cpp:67` |
| `slam_toolbox/clear_changes` | `slam_toolbox/srv/Clear` | `client` | `slam_toolbox_rviz_plugin.cpp:69` |
| `slam_toolbox/manual_loop_closure` | `slam_toolbox/srv/LoopClosure` | `client` | `slam_toolbox_rviz_plugin.cpp:71` |
| `slam_toolbox/save_map` | `slam_toolbox/srv/SaveMap` | `client` | `slam_toolbox_rviz_plugin.cpp:73` |
| `slam_toolbox/clear_queue` | `slam_toolbox/srv/ClearQueue` | `client` | `slam_toolbox_rviz_plugin.cpp:75` |
| `slam_toolbox/toggle_interactive_mode` | `slam_toolbox/srv/ToggleInteractive` | `client` | `slam_toolbox_rviz_plugin.cpp:78` |
| `slam_toolbox/pause_new_measurements` | `slam_toolbox/srv/Pause` | `client` | `slam_toolbox_rviz_plugin.cpp:80` |
| `slam_toolbox/add_submap` | `slam_toolbox/srv/AddSubmap` | `client` | `slam_toolbox_rviz_plugin.cpp:83` |
| `slam_toolbox/merge_submaps` | `slam_toolbox/srv/MergeMaps` | `client` | `slam_toolbox_rviz_plugin.cpp:85` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*