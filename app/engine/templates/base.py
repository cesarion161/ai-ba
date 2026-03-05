from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict

from app.models.workflow_node import NodeType


@dataclass(frozen=True)
class NodeTemplate:
    slug: str
    label: str
    branch: str
    node_type: NodeType
    depends_on: list[str] = field(default_factory=list)
    requires_approval: bool = True
    config: dict | None = None


@dataclass(frozen=True)
class WorkflowTemplate:
    key: str
    label: str
    nodes: list[NodeTemplate]

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        slugs = {n.slug for n in self.nodes}

        # Check for duplicate slugs
        if len(slugs) != len(self.nodes):
            seen: set[str] = set()
            for n in self.nodes:
                if n.slug in seen:
                    raise ValueError(f"Duplicate slug: {n.slug}")
                seen.add(n.slug)

        # Check referential integrity
        for n in self.nodes:
            for dep in n.depends_on:
                if dep not in slugs:
                    raise ValueError(
                        f"Node '{n.slug}' depends on '{dep}' which does not exist"
                    )

        # Cycle detection via topological sort (Kahn's algorithm)
        in_degree: dict[str, int] = defaultdict(int)
        adj: dict[str, list[str]] = defaultdict(list)
        for n in self.nodes:
            in_degree.setdefault(n.slug, 0)
            for dep in n.depends_on:
                adj[dep].append(n.slug)
                in_degree[n.slug] += 1

        queue = [s for s, d in in_degree.items() if d == 0]
        visited = 0
        while queue:
            current = queue.pop(0)
            visited += 1
            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited != len(self.nodes):
            raise ValueError(f"Cycle detected in template '{self.key}'")

    def root_slugs(self) -> list[str]:
        return [n.slug for n in self.nodes if not n.depends_on]
