"""JSON file storage service."""

import json
from pathlib import Path
from typing import Any, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StorageService:
    """Simple JSON file storage with Pydantic models."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, filename: str) -> Path:
        """Get full path for a storage file."""
        return self.data_dir / f"{filename}.json"

    def save(self, filename: str, data: list[BaseModel] | BaseModel) -> None:
        """Save data to JSON file."""
        path = self._get_path(filename)
        if isinstance(data, list):
            json_data = [item.model_dump(mode="json") for item in data]
        else:
            json_data = data.model_dump(mode="json")

        with open(path, "w") as f:
            json.dump(json_data, f, indent=2, default=str)

    def load_list(self, filename: str, model_class: type[T]) -> list[T]:
        """Load list of models from JSON file."""
        path = self._get_path(filename)
        if not path.exists():
            return []

        try:
            with open(path) as f:
                data = json.load(f)
            return [model_class.model_validate(item) for item in data]
        except (json.JSONDecodeError, Exception):
            return []

    def load_single(self, filename: str, model_class: type[T]) -> T | None:
        """Load single model from JSON file."""
        path = self._get_path(filename)
        if not path.exists():
            return None

        try:
            with open(path) as f:
                data = json.load(f)
            return model_class.model_validate(data)
        except (json.JSONDecodeError, Exception):
            return None

    def load_dict(self, filename: str, model_class: type[T]) -> dict[str, T]:
        """Load dict of models from JSON file."""
        path = self._get_path(filename)
        if not path.exists():
            return {}

        try:
            with open(path) as f:
                data = json.load(f)
            return {k: model_class.model_validate(v) for k, v in data.items()}
        except (json.JSONDecodeError, Exception):
            return {}

    def save_dict(self, filename: str, data: dict[str, BaseModel]) -> None:
        """Save dict of models to JSON file."""
        path = self._get_path(filename)
        json_data = {k: v.model_dump(mode="json") for k, v in data.items()}

        with open(path, "w") as f:
            json.dump(json_data, f, indent=2, default=str)

    def delete(self, filename: str) -> bool:
        """Delete a storage file."""
        path = self._get_path(filename)
        if path.exists():
            path.unlink()
            return True
        return False


# Global storage instance
storage = StorageService()
