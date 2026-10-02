"""
Capability Registry & Multidimensional Trait Matrix
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from unimage.protocol.types import TaskType

class ModelCapability(BaseModel):
    model_id: str
    provider: str
    display_name: str
    supported_tasks: List[TaskType]
    
    # Multidimensional Capability Scores (0.0 to 1.0)
    identity_preservation_score: float = Field(ge=0.0, le=1.0)
    text_rendering_score: float = Field(ge=0.0, le=1.0)
    aesthetic_score: float = Field(ge=0.0, le=1.0)
    prompt_adherence_score: float = Field(ge=0.0, le=1.0)
    
    # Performance & Cost Profile
    cost_cents_per_call: float
    typical_latency_ms: int
    
    # Feature Flags
    supports_reference_anchors: bool = False
    supports_inpainting_mask: bool = False
    supports_latent_caching: bool = False
    native_max_resolution: int = 1024

class CapabilityRegistry:
    def __init__(self):
        self._registry: Dict[str, ModelCapability] = {}
        self._init_default_capabilities()

    def register(self, cap: ModelCapability):
        self._registry[cap.model_id] = cap

    def get(self, model_id: str) -> Optional[ModelCapability]:
        return self._registry.get(model_id)

    def list_all(self) -> List[ModelCapability]:
        return list(self._registry.values())

    def _init_default_capabilities(self):
        """Populate realistic models across cloud and local providers"""
        
        # 1. fal.ai / Flux-Schnell (Ultra fast, low cost, decent quality, moderate text)
        self.register(ModelCapability(
            model_id="fal/flux-schnell",
            provider="fal.ai",
            display_name="Black Forest Labs Flux.1 [schnell] via fal.ai",
            supported_tasks=[TaskType.TEXT_TO_IMAGE],
            identity_preservation_score=0.45,
            text_rendering_score=0.88,
            aesthetic_score=0.82,
            prompt_adherence_score=0.85,
            cost_cents_per_call=0.35,
            typical_latency_ms=1200,
            supports_reference_anchors=False,
            supports_inpainting_mask=False,
            supports_latent_caching=False,
            native_max_resolution=1024
        ))

        # 2. fal.ai / Flux-Dev + PuLID (High-tier identity preservation)
        self.register(ModelCapability(
            model_id="fal/flux-dev-pulid",
            provider="fal.ai",
            display_name="Flux.1 [dev] with PuLID Face Anchor",
            supported_tasks=[TaskType.TEXT_TO_IMAGE, TaskType.CHARACTER_CONSISTENT_EDIT],
            identity_preservation_score=0.92,
            text_rendering_score=0.89,
            aesthetic_score=0.90,
            prompt_adherence_score=0.91,
            cost_cents_per_call=2.5,
            typical_latency_ms=4500,
            supports_reference_anchors=True,
            supports_inpainting_mask=True,
            supports_latent_caching=True,
            native_max_resolution=1536
        ))

        # 3. OpenAI DALL-E 3 (High prompt adherence, high cost, low identity anchor)
        self.register(ModelCapability(
            model_id="openai/dall-e-3",
            provider="openai",
            display_name="OpenAI DALL-E 3 Standard",
            supported_tasks=[TaskType.TEXT_TO_IMAGE],
            identity_preservation_score=0.30,
            text_rendering_score=0.92,
            aesthetic_score=0.85,
            prompt_adherence_score=0.95,
            cost_cents_per_call=4.0,
            typical_latency_ms=7500,
            supports_reference_anchors=False,
            supports_inpainting_mask=False,
            supports_latent_caching=False,
            native_max_resolution=1024
        ))

        # 4. Local / Self-Hosted ComfyUI FaceFix & Inpaint Worker (Targeted Repair)
        self.register(ModelCapability(
            model_id="comfy/face-detailer-inpaint",
            provider="comfy_cluster",
            display_name="ComfyUI Segment & FaceDetailer Node Repair",
            supported_tasks=[TaskType.INPAINT_REPAIR, TaskType.CHARACTER_CONSISTENT_EDIT],
            identity_preservation_score=0.96,
            text_rendering_score=0.50,
            aesthetic_score=0.88,
            prompt_adherence_score=0.80,
            cost_cents_per_call=0.6,
            typical_latency_ms=1800,
            supports_reference_anchors=True,
            supports_inpainting_mask=True,
            supports_latent_caching=True,
            native_max_resolution=2048
        ))

        # 5. Local / Self-Hosted ComfyUI 4x UltraSharp Super-Resolution
        self.register(ModelCapability(
            model_id="comfy/ultrasharp-4x",
            provider="comfy_cluster",
            display_name="ComfyUI 4x-UltraSharp Model Upscaler",
            supported_tasks=[TaskType.STYLE_TRANSFER],
            identity_preservation_score=0.98,
            text_rendering_score=0.95,
            aesthetic_score=0.95,
            prompt_adherence_score=0.90,
            cost_cents_per_call=0.4,
            typical_latency_ms=1100,
            supports_reference_anchors=False,
            supports_inpainting_mask=False,
            supports_latent_caching=False,
            native_max_resolution=4096
        ))

# Global registry instance
global_registry = CapabilityRegistry()
