from __future__ import annotations

import pytest


@pytest.fixture
def sample_messages() -> list[dict[str, str]]:
    return [
        {"role": "user", "content": "I'm renovating my kitchen"},
        {"role": "assistant", "content": "What style are you going for?"},
        {"role": "user", "content": "Modern minimalist, white and wood tones"},
    ]
