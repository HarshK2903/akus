"""Refresh the checked-in OpenAPI document after API contract changes."""
import json
from pathlib import Path

from akus.main import create_app

Path(__file__).resolve().parents[1].joinpath('docs/openapi.json').write_text(
    json.dumps(create_app().openapi(), indent=2) + '\n'
)
