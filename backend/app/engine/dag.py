"""DAG validation, cycle detection, topological sorting, and dependency resolution."""

from collections import defaultdict, deque
from typing import Any, Dict, List, Set, Tuple


class DAGValidationError(Exception):
    """Raised when workflow graph structure violates DAG constraints."""
    pass


class DAG:
    """Directed Acyclic Graph compiler for FlowPilot AI workflows."""

    # Keep this registry in sync with ``execute_node``.  A graph must not be
    # allowed to contain nodes the runtime cannot execute.
    NODE_TYPES = {
        "manualtrigger", "trigger", "scheduletrigger", "gmailtrigger",
        "aiagent", "agent", "llmcompletion", "textclassifier", "textsummarizer",
        "dataextractor", "informationextractor", "aidecision", "condition", "transform", "delay", "humanapproval",
        "webhooktrigger",
        "httpintegration", "notification", "output",
    }
    REQUIRED_CONFIG = {
        "scheduletrigger": ("cron",),
        "llmcompletion": ("prompt",),
        "transform": ("mapping",),
        "httpintegration": ("url",),
    }
    PORTS = {
        "condition": {"source": {"true", "false"}, "target": set()},
    }
    DEFAULT_SOURCE_PORTS = {"default", "output", "out"}
    DEFAULT_TARGET_PORTS = {"default", "input", "in"}

    def __init__(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]):
        self.raw_nodes = nodes
        self.raw_edges = edges
        self.node_map: Dict[str, Dict[str, Any]] = {}
        self.adj_list: Dict[str, List[str]] = defaultdict(list)
        self.in_degree: Dict[str, int] = {n["id"]: 0 for n in nodes}
        self.edge_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

        self._build_graph()

    def _build_graph(self):
        for node in self.raw_nodes:
            node_id = node.get("id")
            if not node_id:
                continue
            # Keep the first node so duplicate IDs can be reported by validate.
            if node_id not in self.node_map:
                self.node_map[node_id] = node
        for edge in self.raw_edges:
            src = edge.get("source")
            tgt = edge.get("target")

            if src not in self.node_map:
                raise DAGValidationError(f"Edge references non-existent source node '{src}'")
            if tgt not in self.node_map:
                raise DAGValidationError(f"Edge references non-existent target node '{tgt}'")

            self.adj_list[src].append(tgt)
            self.in_degree[tgt] += 1
            self.edge_map[(src, tgt)] = edge

    def detect_cycles_and_sort(self) -> List[str]:
        """Kahn's algorithm: topological sort and cycle detection."""
        in_deg = self.in_degree.copy()
        queue = deque([node_id for node_id, deg in in_deg.items() if deg == 0])
        sorted_order: List[str] = []

        while queue:
            curr = queue.popleft()
            sorted_order.append(curr)

            for neighbor in self.adj_list[curr]:
                in_deg[neighbor] -= 1
                if in_deg[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_order) != len(self.node_map):
            cycle_nodes = [node_id for node_id, deg in in_deg.items() if deg > 0]
            raise DAGValidationError(f"Cycle detected in workflow graph involving nodes: {cycle_nodes}")

        return sorted_order

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Validate workflow structure and return (is_valid, errors, warnings)."""
        errors: List[str] = []
        warnings: List[str] = []

        if not self.node_map:
            errors.append("Workflow has no nodes.")
            return False, errors, warnings

        ids = [n.get("id") for n in self.raw_nodes]
        if any(not node_id for node_id in ids):
            errors.append("Every node must have a non-empty ID.")
        duplicates = sorted({node_id for node_id in ids if node_id and ids.count(node_id) > 1})
        if duplicates:
            errors.append(f"Node IDs must be unique; duplicates: {duplicates}")

        edge_ids = [e.get("id") for e in self.raw_edges]
        if any(not edge_id for edge_id in edge_ids):
            errors.append("Every edge must have a non-empty ID.")
        duplicate_edges = sorted({edge_id for edge_id in edge_ids if edge_id and edge_ids.count(edge_id) > 1})
        if duplicate_edges:
            errors.append(f"Edge IDs must be unique; duplicates: {duplicate_edges}")

        for node in self.raw_nodes:
            node_type = str(node.get("type", "")).lower()
            if node_type not in self.NODE_TYPES:
                errors.append(f"Node '{node.get('id', '<unknown>')}' uses unregistered type '{node.get('type', '')}'.")
                continue
            config = node.get("config", {})
            if not isinstance(config, dict):
                errors.append(f"Node '{node.get('id', '<unknown>')}' config must be an object.")
                config = {}
            for key in self.REQUIRED_CONFIG.get(node_type, ()):
                if key not in config or config[key] in (None, "", {}):
                    errors.append(f"Node '{node.get('id', '<unknown>')}' requires config field '{key}'.")

        # Check triggers
        trigger_nodes = [
            n for n in self.raw_nodes if n.get("type", "").lower().endswith("trigger")
        ]
        if not trigger_nodes:
            errors.append("Workflow must contain at least one trigger node (e.g., Manual Trigger, Schedule, Gmail).")

        # Cycle check
        try:
            self.detect_cycles_and_sort()
        except DAGValidationError as e:
            errors.append(str(e))

        for edge in self.raw_edges:
            src = self.node_map.get(edge.get("source"))
            if src:
                node_type = str(src.get("type", "")).lower()
                source_handle = edge.get("sourceHandle")
                allowed = self.PORTS.get(node_type, {}).get("source") or self.DEFAULT_SOURCE_PORTS
                if source_handle is not None and source_handle not in allowed:
                    errors.append(
                        f"Edge '{edge.get('id', '<unknown>')}' references invalid source port "
                        f"'{source_handle}' on node '{edge.get('source')}'."
                    )
            target = self.node_map.get(edge.get("target"))
            target_handle = edge.get("targetHandle")
            if target and target_handle is not None and target_handle not in self.DEFAULT_TARGET_PORTS:
                errors.append(
                    f"Edge '{edge.get('id', '<unknown>')}' references invalid target port "
                    f"'{target_handle}' on node '{edge.get('target')}'."
                )

        # Check disconnected non-trigger nodes
        for node_id, deg in self.in_degree.items():
            node = self.node_map[node_id]
            is_trigger = node.get("type", "").lower().endswith("trigger")
            if deg == 0 and not is_trigger and len(self.node_map) > 1:
                warnings.append(f"Node '{node.get('label', node_id)}' has no inputs and is not a trigger.")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def get_upstream_nodes(self, node_id: str) -> List[str]:
        """Return direct parents of node."""
        parents = []
        for (src, tgt) in self.edge_map.keys():
            if tgt == node_id:
                parents.append(src)
        return parents
