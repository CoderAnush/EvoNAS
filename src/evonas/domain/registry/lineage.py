"""Lineage engine — graph over registry objects (metadata traversal only)."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


class LineageEngine:
    """Build and traverse directed lineage edges between governed objects."""

    def __init__(self) -> None:
        self._edges: list[dict[str, str]] = []
        # adjacency: from_id -> list of (to_id, relation)
        self._out: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self._in: dict[str, list[tuple[str, str]]] = defaultdict(list)

    def clear(self) -> None:
        self._edges.clear()
        self._out.clear()
        self._in.clear()

    def link(
        self,
        source_id: str,
        target_id: str,
        *,
        relation: str = "produces",
    ) -> dict[str, str]:
        edge = {
            "source": source_id,
            "target": target_id,
            "relation": relation,
        }
        self._edges.append(edge)
        self._out[source_id].append((target_id, relation))
        self._in[target_id].append((source_id, relation))
        return edge

    def load_edges(self, edges: list[dict[str, Any]]) -> None:
        self.clear()
        for edge in edges:
            self.link(
                str(edge["source"]),
                str(edge["target"]),
                relation=str(edge.get("relation", "produces")),
            )

    def parents_of(self, object_id: str) -> list[dict[str, str]]:
        return [
            {"id": pid, "relation": rel} for pid, rel in self._in.get(object_id, [])
        ]

    def children_of(self, object_id: str) -> list[dict[str, str]]:
        return [
            {"id": cid, "relation": rel} for cid, rel in self._out.get(object_id, [])
        ]

    def ancestors(self, object_id: str, *, max_depth: int = 32) -> list[str]:
        return self._bfs(object_id, self._in, max_depth=max_depth)

    def descendants(self, object_id: str, *, max_depth: int = 32) -> list[str]:
        return self._bfs(object_id, self._out, max_depth=max_depth)

    def subgraph(self, object_id: str, *, max_depth: int = 8) -> dict[str, Any]:
        nodes = {object_id}
        nodes.update(self.ancestors(object_id, max_depth=max_depth))
        nodes.update(self.descendants(object_id, max_depth=max_depth))
        edges = [
            e
            for e in self._edges
            if e["source"] in nodes and e["target"] in nodes
        ]
        return {"root": object_id, "nodes": sorted(nodes), "edges": edges}

    def mermaid(self, object_id: str | None = None, *, max_depth: int = 8) -> str:
        if object_id:
            graph = self.subgraph(object_id, max_depth=max_depth)
            edges = graph["edges"]
        else:
            edges = self._edges
        lines = ["flowchart LR"]
        if not edges:
            nid = object_id or "empty"
            lines.append(f'  {self._safe(nid)}["{nid}"]')
            return "\n".join(lines)
        for edge in edges:
            src = self._safe(edge["source"])
            dst = self._safe(edge["target"])
            rel = edge.get("relation", "produces")
            lines.append(f'  {src}["{edge["source"]}"] -->|{rel}| {dst}["{edge["target"]}"]')
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {"edges": list(self._edges), "node_count": len(set(self._out) | set(self._in))}

    @staticmethod
    def _bfs(
        start: str,
        adj: dict[str, list[tuple[str, str]]],
        *,
        max_depth: int,
    ) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        q: deque[tuple[str, int]] = deque([(start, 0)])
        while q:
            node, depth = q.popleft()
            if depth >= max_depth:
                continue
            for nxt, _rel in adj.get(node, []):
                if nxt in seen or nxt == start:
                    continue
                seen.add(nxt)
                out.append(nxt)
                q.append((nxt, depth + 1))
        return out

    @staticmethod
    def _safe(node_id: str) -> str:
        return "".join(ch if ch.isalnum() else "_" for ch in node_id)[:64] or "n"
