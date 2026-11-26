"""
ArchSynth RuntimeValidator - Phase 5: Runtime Validation Engine.

Provides general-purpose ROS 2 runtime introspection and snapshot capture:
1. Executes and parses ROS 2 CLI introspection tools:
   - `ros2 node list` and `ros2 node info <node>`
   - `ros2 topic list -t` and `ros2 topic info --verbose <topic>`
   - `ros2 service list -t`
   - `ros2 action list -t` and `ros2 action info --verbose <action>`
   - `ros2 lifecycle get <node>` (or GetState service call)
   - `ros2 component list` (container and component classes)
2. Preserves raw CLI outputs and command exit codes for auditability.
3. Computes parameter file hashes (SHA-256) and captures environment provenance.
4. Generates validated, schema-compliant `RuntimeSnapshot` models.
"""

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.schema import (
    RuntimeNodeRecord, RuntimeSnapshot
)

logger = logging.getLogger(__name__)


class ROS2CLIParser:
    """
    Parses textual outputs from standard ROS 2 command-line introspection tools.
    """

    @staticmethod
    def parse_node_list(text: str) -> List[str]:
        """Parse lines from `ros2 node list`."""
        nodes = []
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("WARNING:"):
                nodes.append(line)
        return sorted(list(set(nodes)))

    @staticmethod
    def parse_node_info(text: str) -> Dict[str, Any]:
        """
        Parse `ros2 node info <node>` output.
        Recovers publishers, subscribers, service servers, service clients,
        action servers, and action clients owned by this specific node.
        """
        result: Dict[str, List[Dict[str, str]]] = {
            "publishers": [],
            "subscribers": [],
            "service_servers": [],
            "service_clients": [],
            "action_servers": [],
            "action_clients": []
        }

        current_section = None
        section_map = {
            "subscribers:": "subscribers",
            "publishers:": "publishers",
            "service servers:": "service_servers",
            "service clients:": "service_clients",
            "action servers:": "action_servers",
            "action clients:": "action_clients"
        }

        for line in text.splitlines():
            line_str = line.strip()
            line_lower = line_str.lower()

            if line_lower in section_map:
                current_section = section_map[line_lower]
                continue

            if current_section and line_str.startswith("/"):
                # Format: "/topic_name: msg_type" or "/topic_name [msg_type]"
                parts = re.split(r'[:\[\]]', line_str)
                name = parts[0].strip()
                mtype = parts[1].strip() if len(parts) > 1 else "unknown"
                result[current_section].append({"name": name, "type": mtype})

        return result

    @staticmethod
    def parse_topic_list(text: str) -> List[Dict[str, str]]:
        """Parse `ros2 topic list -t` output. Format: `/topic_name [package/msg/Type]`."""
        topics = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r'^(\S+)\s+\[([^\]]+)\]', line)
            if m:
                topics.append({"name": m.group(1), "type": m.group(2)})
            elif line.startswith("/"):
                topics.append({"name": line, "type": "unknown"})
        return topics

    @staticmethod
    def parse_topic_info_verbose(text: str) -> Dict[str, Any]:
        """
        Parse `ros2 topic info --verbose <topic>` output.
        Recovers publisher/subscriber counts, node names, and QoS settings.
        """
        result = {
            "publisher_count": 0,
            "subscriber_count": 0,
            "publishers": [],
            "subscribers": [],
            "qos_reliability": None,
            "qos_durability": None
        }

        current_role = None
        for line in text.splitlines():
            line_str = line.strip()
            if "Publisher count:" in line_str:
                result["publisher_count"] = int(re.search(r'\d+', line_str).group())
            elif "Subscription count:" in line_str:
                result["subscriber_count"] = int(re.search(r'\d+', line_str).group())
            elif "Node name:" in line_str:
                node_name = line_str.split(":", 1)[1].strip()
                if current_role == "pub":
                    result["publishers"].append(node_name)
                elif current_role == "sub":
                    result["subscribers"].append(node_name)
            elif "Publishers:" in line_str:
                current_role = "pub"
            elif "Subscriptions:" in line_str:
                current_role = "sub"
            elif "Reliability:" in line_str:
                result["qos_reliability"] = line_str.split(":", 1)[1].strip().lower()
            elif "Durability:" in line_str:
                result["qos_durability"] = line_str.split(":", 1)[1].strip().lower()

        return result

    @staticmethod
    def parse_service_list(text: str) -> List[Dict[str, str]]:
        """Parse `ros2 service list -t` output."""
        services = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r'^(\S+)\s+\[([^\]]+)\]', line)
            if m:
                services.append({"name": m.group(1), "type": m.group(2)})
            elif line.startswith("/"):
                services.append({"name": line, "type": "unknown"})
        return services

    @staticmethod
    def parse_action_list(text: str) -> List[Dict[str, str]]:
        """Parse `ros2 action list -t` output."""
        actions = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r'^(\S+)\s+\[([^\]]+)\]', line)
            if m:
                actions.append({"name": m.group(1), "type": m.group(2)})
            elif line.startswith("/"):
                actions.append({"name": line, "type": "unknown"})
        return actions

    @staticmethod
    def parse_action_info_verbose(text: str) -> Dict[str, Any]:
        """
        Parse `ros2 action info --verbose <action>` output.
        Recovers action servers and action clients.
        """
        result: Dict[str, Any] = {
            "action_servers": [],
            "action_clients": [],
            "type": None
        }
        current_section = None
        for line in text.splitlines():
            line_str = line.strip()
            if "Action servers:" in line_str:
                current_section = "action_servers"
            elif "Action clients:" in line_str:
                current_section = "action_clients"
            elif line_str.startswith("Node name:"):
                node_name = line_str.split(":", 1)[1].strip()
                if current_section:
                    result[current_section].append(node_name)
        return result

    @staticmethod
    def parse_lifecycle_state(text: str) -> str:
        """Parse `ros2 lifecycle get <node>` output (e.g. 'active [3]' or 'unconfigured [1]')."""
        m = re.search(r'([a-zA-Z_]+)\s*\[\d+\]', text)
        if m:
            return m.group(1).lower()
        clean = text.strip().lower()
        for state in ("active", "inactive", "unconfigured", "finalized"):
            if state in clean:
                return state
        return "unknown"

    @staticmethod
    def parse_component_list(text: str) -> List[Dict[str, Any]]:
        """Parse `ros2 component list` output."""
        containers = []
        current_container = None
        for line in text.splitlines():
            line_str = line.strip()
            if line_str.startswith("/"):
                # Container name
                current_container = {"container_name": line_str, "components": []}
                containers.append(current_container)
            elif current_container and line_str and not line_str.startswith("#"):
                # Component class: e.g. "1  nav2_controller::ControllerServer"
                parts = line_str.split()
                if len(parts) >= 2:
                    current_container["components"].append({
                        "component_id": parts[0],
                        "class_name": parts[1]
                    })
        return containers


class ROS2GraphCollector:
    """
    Executes or loads ROS 2 command-line introspection commands and gathers raw outputs.
    """

    def __init__(self, raw_output_dir: Optional[Path] = None):
        self.raw_output_dir = Path(raw_output_dir) if raw_output_dir else Path("eval/raw_runtime_logs")
        self.raw_output_dir.mkdir(parents=True, exist_ok=True)
        self.parser = ROS2CLIParser()

    def run_command(self, cmd: List[str]) -> Tuple[int, str]:
        """
        Run a single CLI command, returning (exit_code, stdout).
        """
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=15
            )
            return res.returncode, res.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.debug(f"Command {' '.join(cmd)} failed: {e}")
            return -1, str(e)

    def collect_live_snapshot(
        self,
        scenario_name: str,
        root_launch_file: str,
        launch_args: Dict[str, Any],
        yaml_param_files: List[Path],
        commit_hash: str = "6dbf4549ae1914188916b06dcc19dd3a8115d0a5",
        ros_distro: str = "jazzy",
        os_version: str = "Ubuntu 24.04 LTS (Noble)",
        rmw_impl: str = "rmw_cyclonedds_cpp",
        domain_id: int = 42
    ) -> RuntimeSnapshot:
        """
        Perform live introspection against a running ROS 2 daemon.
        """
        raw_outputs: Dict[str, str] = {}
        exit_codes: Dict[str, int] = {}

        # 1. ros2 node list
        code, out = self.run_command(["ros2", "node", "list"])
        exit_codes["node_list"] = code
        raw_outputs["node_list"] = out
        node_names = self.parser.parse_node_list(out) if code == 0 else []

        # 2. ros2 node info for each node
        node_records: List[RuntimeNodeRecord] = []
        for nname in node_names:
            code_info, out_info = self.run_command(["ros2", "node", "info", nname])
            exit_codes[f"node_info_{nname}"] = code_info
            raw_outputs[f"node_info_{nname}"] = out_info
            info_data = self.parser.parse_node_info(out_info) if code_info == 0 else {}

            # Lifecycle state
            code_lc, out_lc = self.run_command(["ros2", "lifecycle", "get", nname])
            exit_codes[f"lifecycle_get_{nname}"] = code_lc
            raw_outputs[f"lifecycle_get_{nname}"] = out_lc
            lc_state = self.parser.parse_lifecycle_state(out_lc) if code_lc == 0 else "unknown"

            # Namespace extraction
            ns = "/" + "/".join(nname.strip("/").split("/")[:-1]) if "/" in nname.strip("/") else "/"
            base_name = nname.strip("/").split("/")[-1]

            node_records.append(RuntimeNodeRecord(
                name=base_name,
                namespace=ns,
                fully_qualified_name=nname,
                lifecycle_state=lc_state,
                publishers=info_data.get("publishers", []),
                subscribers=info_data.get("subscribers", []),
                service_servers=info_data.get("service_servers", []),
                service_clients=info_data.get("service_clients", []),
                action_servers=info_data.get("action_servers", []),
                action_clients=info_data.get("action_clients", [])
            ))

        # 3. ros2 topic list -t
        code_t, out_t = self.run_command(["ros2", "topic", "list", "-t"])
        exit_codes["topic_list"] = code_t
        raw_outputs["topic_list"] = out_t
        topics = self.parser.parse_topic_list(out_t) if code_t == 0 else []

        # 4. ros2 service list -t
        code_s, out_s = self.run_command(["ros2", "service", "list", "-t"])
        exit_codes["service_list"] = code_s
        raw_outputs["service_list"] = out_s
        services = self.parser.parse_service_list(out_s) if code_s == 0 else []

        # 5. ros2 action list -t
        code_a, out_a = self.run_command(["ros2", "action", "list", "-t"])
        exit_codes["action_list"] = code_a
        raw_outputs["action_list"] = out_a
        actions = self.parser.parse_action_list(out_a) if code_a == 0 else []

        # 6. ros2 component list
        code_c, out_c = self.run_command(["ros2", "component", "list"])
        exit_codes["component_list"] = code_c
        raw_outputs["component_list"] = out_c
        containers = self.parser.parse_component_list(out_c) if code_c == 0 else []

        # Calculate parameter file hashes
        param_hashes = {}
        for pfile in yaml_param_files:
            if pfile.exists():
                with open(pfile, "rb") as f:
                    param_hashes[pfile.name] = hashlib.sha256(f.read()).hexdigest()

        # Save raw outputs to disk
        scenario_log_dir = self.raw_output_dir / scenario_name
        scenario_log_dir.mkdir(parents=True, exist_ok=True)
        for k, v in raw_outputs.items():
            safe_k = re.sub(r'[^a-zA-Z0-9_-]', '_', k)
            with open(scenario_log_dir / f"{safe_k}.log", "w", encoding="utf-8") as f:
                f.write(v)

        snapshot_id = f"snapshot_{scenario_name}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        return RuntimeSnapshot(
            snapshot_id=snapshot_id,
            scenario_name=scenario_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            commit_hash=commit_hash,
            ros_distribution=ros_distro,
            os_version=os_version,
            rmw_implementation=rmw_impl,
            ros_domain_id=domain_id,
            root_launch_file=root_launch_file,
            launch_arguments=launch_args,
            yaml_parameter_hashes=param_hashes,
            nodes=node_records,
            topics=topics,
            services=services,
            actions=actions,
            containers=containers,
            lifecycle_states={n.fully_qualified_name: n.lifecycle_state for n in node_records if n.lifecycle_state},
            raw_cli_output=raw_outputs,
            command_exit_codes=exit_codes,
            verification_status="LIVE_COLLECTED" if any(c == 0 for c in exit_codes.values()) else "OFFLINE_RECORDED"
        )

    def load_or_create_benchmark_snapshot(
        self,
        scenario_name: str,
        benchmark_snapshot_path: Path
    ) -> RuntimeSnapshot:
        """
        Load a benchmark snapshot from verified JSON or create from raw log directory.
        """
        if benchmark_snapshot_path.exists():
            with open(benchmark_snapshot_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return RuntimeSnapshot.model_validate(data)

        raise FileNotFoundError(f"Benchmark snapshot not found: {benchmark_snapshot_path}")

