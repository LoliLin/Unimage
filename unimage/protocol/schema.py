"""
Capability-based Declarative Media Protocol (CDMP) - Pydantic Schema Specification
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

from unimage.protocol.types import TaskType, AnchorType, FidelityLevel, StepStatus, RoutingStrategy

class Dimensions(BaseModel):
    width: int = Field(default=1024, ge=256, le=4096)
    height: int = Field(default=1024, ge=256, le=4096)

class MediaAnchor(BaseModel):
    id: str = Field(default_factory=lambda: f"anchor_{uuid.uuid4().hex[:6]}")
    type: AnchorType
    source_uri: str = Field(description="URI or base64 data for reference anchor asset")
    target_region: Optional[str] = Field(default="global", description="e.g. 'face', 'background', 'hands', 'global'")
    fidelity: FidelityLevel = Field(default=FidelityLevel.STANDARD)
    influence_weight: float = Field(default=0.8, ge=0.0, le=1.0)

class QualityThresholds(BaseModel):
    face_similarity: Optional[float] = Field(default=0.80, ge=0.0, le=1.0)
    text_rendering_accuracy: Optional[float] = Field(default=0.85, ge=0.0, le=1.0)
    aesthetic_score: Optional[float] = Field(default=0.70, ge=0.0, le=1.0)
    prompt_adherence: Optional[float] = Field(default=0.75, ge=0.0, le=1.0)

class MediaRequirements(BaseModel):
    dimensions: Dimensions = Field(default_factory=Dimensions)
    max_latency_ms: int = Field(default=8000, description="Hard SLA timeout in milliseconds")
    max_cost_cents: float = Field(default=10.0, description="Budget ceiling in US cents")
    routing_strategy: RoutingStrategy = Field(default=RoutingStrategy.PARETO_OPTIMAL)
    quality_thresholds: QualityThresholds = Field(default_factory=QualityThresholds)

class LifecyclePolicy(BaseModel):
    retain_intermediate_latents: bool = Field(default=True, description="Keep latents in fast store for multi-turn editing")
    allow_saga_repair: bool = Field(default=True, description="Enable transactional repair loops if evaluation falls below SLA")
    max_repair_passes: int = Field(default=2, ge=0, le=5)
    ttl_seconds: int = Field(default=3600, description="Retention time for session assets")

class MediaIntent(BaseModel):
    task: TaskType
    action: str = Field(description="Semantic action name, e.g. 'scene_transfer', 'generate_character', 'expand_view'")
    prompt: str = Field(description="Core generative prompt")
    negative_prompt: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DeclarativeMediaRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:12]}")
    intent: MediaIntent
    anchors: List[MediaAnchor] = Field(default_factory=list)
    requirements: MediaRequirements = Field(default_factory=MediaRequirements)
    lifecycle_policy: LifecyclePolicy = Field(default_factory=LifecyclePolicy)

class StepTrace(BaseModel):
    step_id: str
    operator_name: str
    provider: str
    model: str
    status: StepStatus
    duration_ms: int
    cost_cents: float
    output_asset_uri: Optional[str] = None
    intermediate_latent_ref: Optional[str] = None
    evaluation_metrics: Dict[str, float] = Field(default_factory=dict)
    notes: Optional[str] = None

class ExecutionResult(BaseModel):
    request_id: str
    final_asset_uri: str
    status: StepStatus
    total_latency_ms: int
    total_cost_cents: float
    repaired_passes: int = 0
    sla_passed: bool
    evaluation_summary: Dict[str, float]
    execution_trace: List[StepTrace]
    session_latent_key: Optional[str] = None
