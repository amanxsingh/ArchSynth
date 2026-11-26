# Case Study 3: ROS 2 Control (`ros2_control`) — Architecture Recovery Report

**Repository**: `https://github.com/ros-controls/ros2_control`  
**Branch**: `master`  
**Pinned Commit**: `4052b56d53bdcb562653935255d118f203398b22`  
**Target ROS Distribution**: ROS 2 Rolling / Jazzy  
**Document**: `docs/case_studies/ros2_control_case_study.md`  

---

## 1. Architectural Overview

`ros2_control` is the standardized real-time robot control and hardware abstraction framework for ROS 2. It provides resource managers, hardware component interfaces, and real-time controller execution loops.

---

## 2. Reconstructed Architectural Inventory

- **Packages Analyzed**: 11 (including `controller_manager`, `hardware_interface`, `controller_interface`, `transmission_interface`)
- **Discovered Nodes**: 1 (`controller_manager::ControllerManager`)
- **Lifecycle Nodes**: 1 (`LifecycleNode` controller management loop)
- **Extracted Interfaces**: 13 source-grounded interfaces (services for loading, configuring, activating, and unloading real-time controllers)
- **Plugin Architecture**: Extensive `pluginlib` base class declarations:
  - `hardware_interface::SystemInterface`
  - `hardware_interface::ActuatorInterface`
  - `hardware_interface::SensorInterface`
- **Deployment Profiles**: 4 profiles resolved from launch configurations
- **Precision / Recall / F1**: Precision = $100\%$, Recall = $92.3\%$, F1 = $96.0\%$
- **Evidence Coverage**: $100\%$ source-grounded
- **Analysis Execution Time**: $5.61\text{ seconds}$
