"""
OpenAI Image API Ingress Polyfill (Backward Compatibility Layer)
Allows LangChain, AutoGen, and OpenAI SDKs to talk directly to Unimage without code changes.
"""

import time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from unimage.protocol.schema import (
    DeclarativeMediaRequest,
    MediaIntent,
    MediaAnchor,
    MediaRequirements,
    Dimensions,
    QualityThresholds
)
from unimage.protocol.types import TaskType, AnchorType, FidelityLevel, RoutingStrategy
from unimage.client import UnimageClient

router = APIRouter(tags=["OpenAI Compatibility Layer"])
client = UnimageClient()

# OpenAI Request Schemas
class OpenAIImageGenerationRequest(BaseModel):
    prompt: str
    model: Optional[str] = "dall-e-3"
    n: Optional[int] = 1
    quality: Optional[str] = "standard"  # 'standard' or 'hd'
    response_format: Optional[str] = "url"
    size: Optional[str] = "1024x1024"
    style: Optional[str] = "vivid"
    user: Optional[str] = None

class OpenAIImageEditRequest(BaseModel):
    image: str = Field(description="Base64 encoded string or URL to the source image")
    prompt: str
    mask: Optional[str] = None
    model: Optional[str] = "dall-e-2"
    n: Optional[int] = 1
    size: Optional[str] = "1024x1024"
    response_format: Optional[str] = "url"
    user: Optional[str] = None

# OpenAI Response Schemas
class OpenAIImageData(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None

class OpenAIImageResponse(BaseModel):
    created: int
    data: List[OpenAIImageData]
    unimage_meta: Optional[Dict[str, Any]] = None

def _parse_size(size_str: Optional[str]) -> Dimensions:
    if not size_str or "x" not in size_str:
        return Dimensions(width=1024, height=1024)
    try:
        w, h = map(int, size_str.split("x"))
        return Dimensions(width=w, height=h)
    except Exception:
        return Dimensions(width=1024, height=1024)

@router.post("/v1/images/generations", response_model=OpenAIImageResponse)
async def openai_images_generations(body: OpenAIImageGenerationRequest):
    """
    OpenAI Compatibility Ingress:
    Intercepts POST /v1/images/generations, upgrades to CDMP, executes through Unimage DAG,
    and returns exact OpenAI specification.
    """
    dims = _parse_size(body.size)
    is_hd = (body.quality == "hd")

    # Map OpenAI request -> DeclarativeMediaRequest
    cdmp_req = DeclarativeMediaRequest(
        intent=MediaIntent(
            task=TaskType.TEXT_TO_IMAGE,
            action="generate",
            prompt=body.prompt
        ),
        requirements=MediaRequirements(
            dimensions=dims,
            routing_strategy=RoutingStrategy.MAX_QUALITY if is_hd else RoutingStrategy.PARETO_OPTIMAL,
            quality_thresholds=QualityThresholds(
                aesthetic_score=0.85 if is_hd else 0.70
            )
        )
    )

    result = await client.dispatch(cdmp_req)

    return OpenAIImageResponse(
        created=int(time.time()),
        data=[
            OpenAIImageData(
                url=result.final_asset_uri,
                revised_prompt=body.prompt
            )
        ],
        unimage_meta={
            "request_id": result.request_id,
            "total_latency_ms": result.total_latency_ms,
            "total_cost_cents": result.total_cost_cents,
            "repaired_passes": result.repaired_passes,
            "sla_passed": result.sla_passed,
            "latent_cache_key": result.session_latent_key
        }
    )

@router.post("/v1/images/edits", response_model=OpenAIImageResponse)
async def openai_images_edits(body: OpenAIImageEditRequest):
    """
    OpenAI Compatibility Ingress:
    Intercepts POST /v1/images/edits, registers source image as Anchor,
    executes targeted edit, and returns standard OpenAI payload.
    """
    dims = _parse_size(body.size)
    
    cdmp_req = DeclarativeMediaRequest(
        intent=MediaIntent(
            task=TaskType.CHARACTER_CONSISTENT_EDIT if "face" in body.prompt.lower() or "character" in body.prompt.lower() else TaskType.INPAINT_REPAIR,
            action="edit",
            prompt=body.prompt
        ),
        anchors=[
            MediaAnchor(
                type=AnchorType.IDENTITY,
                source_uri=body.image,
                target_region="face" if "face" in body.prompt.lower() else "global",
                fidelity=FidelityLevel.STRICT
            )
        ],
        requirements=MediaRequirements(
            dimensions=dims,
            quality_thresholds=QualityThresholds(face_similarity=0.85)
        )
    )

    result = await client.dispatch(cdmp_req)

    return OpenAIImageResponse(
        created=int(time.time()),
        data=[
            OpenAIImageData(
                url=result.final_asset_uri,
                revised_prompt=body.prompt
            )
        ],
        unimage_meta={
            "request_id": result.request_id,
            "repaired_passes": result.repaired_passes,
            "sla_passed": result.sla_passed,
            "total_cost_cents": result.total_cost_cents
        }
    )
