# Node Specification: `controller_manager`

- **Stable Unique ID**: `controller_manager::ControllerManager`
- **Fully Qualified Name**: `controller_manager/controller_manager`
- **Class / Executable**: `controller_manager::ControllerManager`
- **Package**: `controller_manager`
- **Namespace**: `controller_manager`
- **Source File**: `controller_manager/src/controller_manager.cpp`
- **Architectural Classification**: `control`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `controller_manager/include/controller_manager/controller_manager.hpp` | `L65` | `node_definition` | `cpp_ast_analyzer` | 1.0 |
| `controller_manager/src/controller_manager.cpp` | `L531` | `node_definition` | `cpp_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `~/activity` | `controller_manager_msgs/msg/ControllerManagerActivity` | `MessageType.UNKNOWN` | `default` | `controller_manager.cpp:657` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `robot_description` | `std_msgs/msg/String` | `MessageType.UNKNOWN` | `default` | `controller_manager.cpp:754` |

## Services

| Service Name | Type | Role | Evidence |
| :--- | :--- | :--- | :--- |
| `~/list_controllers` | `controller_manager_msgs/srv/ListControllers` | `server` | `controller_manager.cpp:1170` |
| `~/list_controller_types` | `controller_manager_msgs/srv/ListControllerTypes` | `server` | `controller_manager.cpp:1174` |
| `~/load_controller` | `controller_manager_msgs/srv/LoadController` | `server` | `controller_manager.cpp:1178` |
| `~/configure_controller` | `controller_manager_msgs/srv/ConfigureController` | `server` | `controller_manager.cpp:1181` |
| `~/reload_controller_libraries` | `controller_manager_msgs/srv/ReloadControllerLibraries` | `server` | `controller_manager.cpp:1186` |
| `~/switch_controller` | `controller_manager_msgs/srv/SwitchController` | `server` | `controller_manager.cpp:1190` |
| `~/unload_controller` | `controller_manager_msgs/srv/UnloadController` | `server` | `controller_manager.cpp:1194` |
| `~/cleanup_controller` | `controller_manager_msgs/srv/CleanupController` | `server` | `controller_manager.cpp:1198` |
| `~/list_hardware_components` | `controller_manager_msgs/srv/ListHardwareComponents` | `server` | `controller_manager.cpp:1203` |
| `~/list_hardware_interfaces` | `controller_manager_msgs/srv/ListHardwareInterfaces` | `server` | `controller_manager.cpp:1208` |
| `~/set_hardware_component_state` | `controller_manager_msgs/srv/SetHardwareComponentState` | `server` | `controller_manager.cpp:1213` |

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*