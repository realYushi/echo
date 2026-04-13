from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.services.session import clear_sessions

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def reset_sessions() -> Generator[None, None, None]:
    clear_sessions()
    yield
    clear_sessions()


@pytest.fixture
def sample_messages() -> list[dict[str, str]]:
    return [
        {"role": "user", "content": "I'm renovating my kitchen"},
        {"role": "assistant", "content": "What style are you going for?"},
        {"role": "user", "content": "Modern minimalist, white and wood tones"},
    ]
