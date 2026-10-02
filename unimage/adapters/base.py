"""
Base Provider Adapter Interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from unimage.compiler.optimizer import PhysicalStep
from unimage.protocol.types import StepStatus

class StepExecutionOutput(BaseModel):
    step_id: str
    status: StepStatus
    output_asset_uri: str
    intermediate_latent_ref: Optional[str] = None
    mask_uri: Optional[str] = None
    actual_latency_ms: int
    actual_cost_cents: float
    raw_response: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None

class BaseModelAdapter(ABC):
    @abstractmethod
    async def execute(self, step: PhysicalStep, context: Dict[str, Any]) -> StepExecutionOutput:
        """Execute physical step on remote API or local worker"""
        pass
