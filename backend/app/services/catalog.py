from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.data.products import SEED_PRODUCTS
from app.exceptions import ExternalServiceError
from app.utils.embeddings import get_clip_embedding

if TYPE_CHECKING:
    from qdrant_client import AsyncQdrantClient

logger = structlog.get_logger(__name__)

_VECTOR_SIZE = 512


def _product_id_to_uuid(product_id: str) -> str:
    """Deterministic UUID from a product ID string."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, product_id))


async def seed_catalog(
    qdrant_client: AsyncQdrantClient,
    collection: str,
) -> int:
    """Seed the product catalog into Qdrant. Returns number of products seeded."""
    await logger.ainfo("catalog_seed_start", product_count=len(SEED_PRODUCTS), collection=collection)

    try:
        collections = await qdrant_client.get_collections()
        existing_names = [c.name for c in collections.collections]
        if collection not in existing_names:
            await qdrant_client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=_VECTOR_SIZE, distance=Distance.COSINE),
            )
            await logger.ainfo("catalog_collection_created", collection=collection)
    except Exception as exc:
        await logger.aerror("qdrant_collection_creation_failed", exc_info=exc)
        raise ExternalServiceError("qdrant", "Failed to create collection") from exc

    points: list[PointStruct] = []
    for product in SEED_PRODUCTS:
        await logger.adebug("catalog_embedding_product", product_id=product.id, name=product.name)
        embedding = await get_clip_embedding(product.description)
        point = PointStruct(
            id=_product_id_to_uuid(product.id),
            vector=embedding,
            payload=product.model_dump(),
        )
        points.append(point)

    try:
        await qdrant_client.upsert(collection_name=collection, points=points)
    except Exception as exc:
        await logger.aerror("qdrant_product_upsert_failed", exc_info=exc)
        raise ExternalServiceError("qdrant", "Failed to upsert products") from exc

    await logger.ainfo("catalog_seed_complete", seeded=len(points), collection=collection)
    return len(points)
