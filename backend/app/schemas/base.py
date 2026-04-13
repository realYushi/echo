from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model that accepts and emits camelCase at the API boundary."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
