"""
Unimage Workflow Compiler - Physical Optimizer & Pareto Solver
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from unimage.protocol.types import RoutingStrategy, TaskType
from unimage.protocol.schema import DeclarativeMediaRequest
from unimage.registry.capability_matrix import CapabilityRegistry, ModelCapability, global_registry
from unimage.compiler.planner import LogicalPlan, LogicalStep, LogicalOperatorType

class PhysicalStep(BaseModel):
    step_id: str
    logical_operator: str
    selected_model_id: str
    provider: str
    description: str
    estimated_cost_cents: float
    estimated_latency_ms: int
    parameters: Dict[str, Any] = Field(default_factory=dict)
    fallback_model_id: Optional[str] = None
    is_conditional: bool = False
    condition_metric: Optional[str] = None
    condition_threshold: Optional[float] = None

class PhysicalExecutionPlan(BaseModel):
    plan_id: str
    request_id: str
    routing_strategy: RoutingStrategy
    total_estimated_cost_cents: float
    total_estimated_latency_ms: int
    physical_steps: List[PhysicalStep]

class PhysicalOptimizer:
    """
    Cost-Based & SLA Optimizer (CBO) that maps Logical Operators to concrete Physical Model Endpoints.
    """

    def __init__(self, registry: Optional[CapabilityRegistry] = None):
        self.registry = registry or global_registry

    def optimize(self, logical_plan: LogicalPlan, request: DeclarativeMediaRequest) -> PhysicalExecutionPlan:
        physical_steps: List[PhysicalStep] = []
        total_cost = 0.0
        total_latency = 0
        strategy = request.requirements.routing_strategy
        budget_cents = request.requirements.max_cost_cents

        for l_step in logical_plan.steps:
            if l_step.operator_type == LogicalOperatorType.BASE_SYNTHESIS:
                # Need model supporting text_to_image or character edit
                has_anchors = len(l_step.required_anchors) > 0
                candidate = self._select_synthesis_model(has_anchors, strategy, budget_cents)
                
                p_step = PhysicalStep(
                    step_id=l_step.step_id,
                    logical_operator=l_step.operator_type,
                    selected_model_id=candidate.model_id,
                    provider=candidate.provider,
                    description=f"Execute {candidate.display_name} for base synthesis",
                    estimated_cost_cents=candidate.cost_cents_per_call,
                    estimated_latency_ms=candidate.typical_latency_ms,
                    parameters=l_step.parameters,
                    fallback_model_id="openai/dall-e-3" if candidate.model_id != "openai/dall-e-3" else "fal/flux-schnell"
                )
                total_cost += candidate.cost_cents_per_call
                total_latency += candidate.typical_latency_ms
                physical_steps.append(p_step)

            elif l_step.operator_type == LogicalOperatorType.EVALUATION_GATE:
                # Evaluation step
                p_step = PhysicalStep(
                    step_id=l_step.step_id,
                    logical_operator=l_step.operator_type,
                    selected_model_id="evaluator/arcface_clip_vqa",
                    provider="unimage_eval_subsystem",
                    description="Evaluate facial similarity embedding & CLIP aesthetic score",
                    estimated_cost_cents=0.05,
                    estimated_latency_ms=180,
                    parameters=l_step.parameters
                )
                total_cost += 0.05
                total_latency += 180
                physical_steps.append(p_step)

            elif l_step.operator_type == LogicalOperatorType.SAGA_REPAIR_PATCH:
                # Select inpaint / repair model
                repair_candidate = self.registry.get("comfy/face-detailer-inpaint")
                cost = repair_candidate.cost_cents_per_call if repair_candidate else 0.6
                lat = repair_candidate.typical_latency_ms if repair_candidate else 1800

                p_step = PhysicalStep(
                    step_id=l_step.step_id,
                    logical_operator=l_step.operator_type,
                    selected_model_id=repair_candidate.model_id if repair_candidate else "comfy/face-detailer-inpaint",
                    provider=repair_candidate.provider if repair_candidate else "comfy_cluster",
                    description="Apply targeted inpainting repair on facial mask if similarity threshold breaches SLA",
                    estimated_cost_cents=cost,
                    estimated_latency_ms=lat,
                    parameters=l_step.parameters,
                    is_conditional=True,
                    condition_metric=l_step.condition_metric,
                    condition_threshold=l_step.condition_threshold
                )
                total_cost += cost
                total_latency += lat
                physical_steps.append(p_step)

            elif l_step.operator_type == LogicalOperatorType.POST_UPSCALE:
                upscaler = self.registry.get("comfy/ultrasharp-4x")
                cost = upscaler.cost_cents_per_call if upscaler else 0.4
                lat = upscaler.typical_latency_ms if upscaler else 1100

                p_step = PhysicalStep(
                    step_id=l_step.step_id,
                    logical_operator=l_step.operator_type,
                    selected_model_id=upscaler.model_id if upscaler else "comfy/ultrasharp-4x",
                    provider=upscaler.provider if upscaler else "comfy_cluster",
                    description="High-resolution latent tensor upscaling via 4x-UltraSharp",
                    estimated_cost_cents=cost,
                    estimated_latency_ms=lat,
                    parameters=l_step.parameters
                )
                total_cost += cost
                total_latency += lat
                physical_steps.append(p_step)

        return PhysicalExecutionPlan(
            plan_id=f"phys_{logical_plan.plan_id}",
            request_id=request.request_id,
            routing_strategy=strategy,
            total_estimated_cost_cents=round(total_cost, 2),
            total_estimated_latency_ms=total_latency,
            physical_steps=physical_steps
        )

    def _select_synthesis_model(self, has_anchors: bool, strategy: RoutingStrategy, budget: float) -> ModelCapability:
        """Select best candidate model based on anchors and strategy"""
        if has_anchors:
            # Need model with anchor support
            candidate = self.registry.get("fal/flux-dev-pulid")
            if candidate and candidate.cost_cents_per_call <= budget:
                return candidate
            # Fallback
            return self.registry.get("fal/flux-schnell") or self.registry.list_all()[0]
        else:
            if strategy == RoutingStrategy.LOWEST_COST:
                return self.registry.get("fal/flux-schnell") or self.registry.list_all()[0]
            elif strategy == RoutingStrategy.MAX_QUALITY:
                return self.registry.get("openai/dall-e-3") or self.registry.get("fal/flux-dev-pulid")
            else: # PARETO_OPTIMAL
                return self.registry.get("fal/flux-dev-pulid") or self.registry.get("fal/flux-schnell")
