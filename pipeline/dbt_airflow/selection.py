"""Pure graph and trigger validation shared by tasks and QA."""

from __future__ import annotations


class Selection:
    def __init__(self, manifest: dict):
        self.nodes = {**manifest["nodes"], **manifest.get("sources", {})}
        self.models = {
            uid: node
            for uid, node in self.nodes.items()
            if node["resource_type"] == "model" and node["config"].get("enabled", True)
        }
        self.external_models = {
            uid
            for uid, node in self.models.items()
            if "mlit_zoning_core" in node.get("tags", [])
        }
        self.names = {node["name"]: uid for uid, node in self.models.items()}
        self.tests = {
            uid: node
            for uid, node in self.nodes.items()
            if node["resource_type"] == "test"
        }
        self.units = manifest.get("unit_tests", {})

    def ancestors(self, uid: str) -> set[str]:
        result = set()
        pending = list(self.nodes[uid].get("depends_on", {}).get("nodes", []))
        while pending:
            parent = pending.pop()
            if parent not in result and parent in self.nodes:
                result.add(parent)
                pending.extend(
                    self.nodes[parent].get("depends_on", {}).get("nodes", [])
                )
        return result

    def resolve(self, conf: dict) -> tuple[str, set[str]]:
        mode = conf.get("mode", "load_and_transform")
        if mode not in ("load_and_transform", "dbt_only"):
            raise ValueError("mode must be load_and_transform or dbt_only")
        name = conf.get("model")
        if name is not None:
            if mode != "dbt_only":
                raise ValueError("model can only be used with mode=dbt_only")
            if not isinstance(name, str) or name not in self.names:
                raise ValueError(
                    f"Unknown enabled model {name!r}; valid names: {', '.join(sorted(self.names))}"
                )
            uid = self.names[name]
            if uid in self.external_models:
                raise ValueError(
                    "MLIT snapshot models are owned by mlit_zoning_refresh"
                )
            selected = {
                mid for mid in self.models if mid == uid or uid in self.ancestors(mid)
            }
        else:
            selected = set(self.models)
        return mode, selected - self.external_models

    def test_is_selected(self, uid: str, selected: set[str]) -> bool:
        if "mlit_zoning_core" in self.tests[uid].get("tags", []):
            return False
        parents = set(self.tests[uid]["depends_on"]["nodes"])
        # Raw/seed checks and self-contained scenario tests run in every transformation.
        return not parents.intersection(self.models) or bool(
            parents.intersection(selected)
        )

    def reused_relations(self, selected: set[str]) -> set[str]:
        required = set()
        for uid in selected:
            required.update(self.nodes[uid]["depends_on"]["nodes"])
        for uid, node in self.tests.items():
            if self.test_is_selected(uid, selected):
                required.update(node["depends_on"]["nodes"])
        # Check raw/seed even when a partial branch does not directly read them.
        required.update(
            uid
            for uid, n in self.nodes.items()
            if n["resource_type"] in {"source", "seed"}
        )
        return {
            uid
            for uid in required - selected
            if uid in self.nodes
            and self.nodes[uid].get("relation_name")
            and self.nodes[uid].get("config", {}).get("materialized") != "ephemeral"
        }


def batch_failures(summary: dict | None) -> list[int]:
    return [
        item["batch_id"]
        for item in (summary or {}).get("results", [])
        if item.get("status") == "failed"
    ]


def execution_failures(instances, report_id="report_batch_failures") -> list[str]:
    return [
        ti.task_id
        for ti in instances
        if ti.task_id != report_id and ti.state in {"failed", "upstream_failed"}
    ]
