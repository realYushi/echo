from __future__ import annotations

import asyncio
import threading
from typing import Any

import open_clip  # type: ignore[import-untyped]  # open_clip has no type stubs
import structlog
import torch

from app.exceptions import ExternalServiceError

logger = structlog.get_logger(__name__)

# ── Lazy singleton for CLIP model ──────────────────────────────
# open_clip tokenizer type is not exported in stubs; use Any for the module-level cache
_model: torch.nn.Module | None = None
_tokenizer: Any = None
_lock = threading.Lock()


def _load_model() -> tuple[torch.nn.Module, Any]:
    """Load the CLIP model and tokenizer once (thread-safe).

    Returns ``(model, tokenizer)`` -- tokenizer is typed as ``Any`` because
    open_clip does not ship type stubs.
    """
    global _model, _tokenizer  # noqa: PLW0603
    if _model is None or _tokenizer is None:
        with _lock:
            # Double-check after acquiring lock
            if _model is None or _tokenizer is None:
                _model, _, _ = open_clip.create_model_and_transforms(
                    "ViT-B-32",
                    pretrained="laion2b_s34b_b79k",
                )
                _model.eval()
                _tokenizer = open_clip.get_tokenizer("ViT-B-32")
    return _model, _tokenizer


def _encode_text_sync(text: str) -> list[float]:
    """Synchronous CLIP text encoding. Run via asyncio.to_thread()."""
    try:
        model, tokenizer = _load_model()
        tokens = tokenizer([text])
        with torch.no_grad():
            text_features = model.encode_text(tokens)  # type: ignore[operator]  # Module.__getattr__ returns Tensor; encode_text is callable
            text_features /= text_features.norm(dim=-1, keepdim=True)
        embedding: list[float] = text_features[0].tolist()
        return embedding
    except ExternalServiceError:
        raise
    except Exception as exc:
        logger.error("clip_text_encoding_failed", exc_info=exc)
        raise ExternalServiceError("clip", "Failed to encode text") from exc


async def get_clip_embedding(text: str) -> list[float]:
    """Generate CLIP embedding for text input.

    Returns a 512-dimensional float vector. Runs synchronous CLIP
    inference in a thread pool to avoid blocking the event loop.
    """
    return await asyncio.to_thread(_encode_text_sync, text)
