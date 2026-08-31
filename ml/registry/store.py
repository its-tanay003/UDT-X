"""UDT-X ML Local Registry & Metadata Store.

Manages registered model artifacts, metadata, evaluation metrics, and versioning.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("udtx.ml.registry")


class ModelRegistry:
    """Lightweight local model registry for experiment tracking and artifacts."""

    def __init__(self, registry_dir: str | Path = "ml/registry") -> None:
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.registry_dir / "registry_index.json"
        self._init_index()

    def _init_index(self) -> None:
        if not self.index_file.exists():
            self._save_index({"models": {}, "latest_version": None})

    def _load_index(self) -> dict[str, Any]:
        try:
            with open(self.index_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"models": {}, "latest_version": None}

    def _save_index(self, data: dict[str, Any]) -> None:
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def log_run(
        self,
        model_name: str,
        version: str,
        datasets: list[str],
        features: list[str],
        metrics: dict[str, float],
        parameters: dict[str, Any],
        model_artifact_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Record an experiment run and register model version."""
        index = self._load_index()
        run_record = {
            "model_name": model_name,
            "version": version,
            "registered_at": datetime.now(UTC).isoformat(),
            "datasets": datasets,
            "features": features,
            "metrics": metrics,
            "parameters": parameters,
            "artifact_path": str(model_artifact_path) if model_artifact_path else None,
        }

        if model_name not in index["models"]:
            index["models"][model_name] = {}

        index["models"][model_name][version] = run_record
        index["latest_version"] = version
        self._save_index(index)

        logger.info(
            "Logged run for model %s (v%s) with metrics: %s",
            model_name,
            version,
            metrics,
        )
        return run_record

    def get_latest_model_meta(
        self, model_name: str = "udtx_ensemble"
    ) -> dict[str, Any] | None:
        """Fetch latest registered model metadata."""
        index = self._load_index()
        models = index.get("models", {}).get(model_name, {})
        if not models:
            return None
        latest_ver = index.get("latest_version")
        if latest_ver and latest_ver in models:
            return models[latest_ver]
        # Return last registered
        last_key = list(models.keys())[-1]
        return models[last_key]
