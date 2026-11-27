# Node Specification: `depth_image_remaper`

- **Stable Unique ID**: `jaco2_gazebo::DepthImageRemap`
- **Fully Qualified Name**: `depth_image_remaper`
- **Class / Executable**: `DepthImageRemap`
- **Package**: `jaco2_gazebo`
- **Namespace**: `/`
- **Source File**: `jaco2_gazebo/scripts/depth_image_remap.py`
- **Architectural Classification**: `unknown`
- **Is Test Entity**: `False`
- **Is Lifecycle Node**: `False`
- **Validation Status**: `supported`

## Evidence / Provenance

| File | Lines | Evidence Type | Source | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `jaco2_gazebo/scripts/depth_image_remap.py` | `L10–L48` | `node_definition` | `python_ast_analyzer` | 1.0 |

## Publishers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `/rgbd_camera/corrected_depth_image` | `Image` | `MessageType.UNKNOWN` | `10` | `depth_image_remap.py:25` |

## Subscribers

| Topic | Message Type | Category | QoS Profile | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `/rgbd_camera/depth_image` | `Image` | `MessageType.UNKNOWN` | `self.image_callback` | `depth_image_remap.py:19` |

## Services

*No services declared.*

## Actions

*No actions declared.*

## Parameters

*No parameters declared.*