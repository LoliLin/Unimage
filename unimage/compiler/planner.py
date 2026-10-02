"""
Unimage Workflow Compiler - Logical Execution Planner
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from unimage.protocol.types import TaskType, AnchorType, StepStatus
from unimage.protocol.schema import DeclarativeMediaRequest, MediaAnchor

class LogicalOperatorType:
    BASE_SYNTHESIS = "base_synthesis"
    IDENTITY_INJECTION = "identity_injection"
    EVALUATION_GATE = "evaluation_gate"
    SAGA_REPAIR_PATCH = "saga_repair_patch"
    POST_UPSCALE = "post_upscale"

class LogicalStep(BaseModel):
    step_id: str
    operator_type: str
    description: str
    required_anchors: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    is_conditional: bool = False
    condition_metric: Optional[str] = None
    condition_threshold: Optional[float] = None

class LogicalPlan(BaseModel):
    plan_id: str
    request_id: str
    steps: List[LogicalStep]

class LogicalPlanner:
    """
    Translates a DeclarativeMediaRequest into a sequence of abstract logical operators.
    Similar to a database query planner converting SQL AST into a Logical Relational Plan.
    """

    def plan(self, request: DeclarativeMediaRequest) -> LogicalPlan:
        steps: List[LogicalStep] = []
        step_idx = 1
        
        # Check anchors
        identity_anchors = [a for a in request.anchors if a.type == AnchorType.IDENTITY]
        has_identity_anchor = len(identity_anchors) > 0
        
        # Step 1: Base Synthesis or Conditioned Generation
        if has_identity_anchor:
            anchor_ids = [a.id for a in identity_anchors]
            steps.append(LogicalStep(
                step_id=f"step_{step_idx:02d}_base_conditioned_synthesis",
                operator_type=LogicalOperatorType.BASE_SYNTHESIS,
                description=f"Generate initial frame conditioned on {len(identity_anchors)} identity anchor(s)",
                required_anchors=anchor_ids,
                parameters={
                    "prompt": request.intent.prompt,
                    "negative_prompt": request.intent.negative_prompt,
                    "target_region": "face"
                }
            ))
        else:
            steps.append(LogicalStep(
                step_id=f"step_{step_idx:02d}_base_synthesis",
                operator_type=LogicalOperatorType.BASE_SYNTHESIS,
                description="Generate initial unconditioned canvas from prompt",
                parameters={
                    "prompt": request.intent.prompt,
                    "negative_prompt": request.intent.negative_prompt
                }
            ))
        step_idx += 1

        # Step 2: Quality & Fidelity Evaluation Gate
        eval_metrics = {}
        if has_identity_anchor and request.requirements.quality_thresholds.face_similarity is not None:
            eval_metrics["face_similarity"] = request.requirements.quality_thresholds.face_similarity
        if request.requirements.quality_thresholds.aesthetic_score is not None:
            eval_metrics["aesthetic_score"] = request.requirements.quality_thresholds.aesthetic_score

        steps.append(LogicalStep(
            step_id=f"step_{step_idx:02d}_quality_eval_gate",
            operator_type=LogicalOperatorType.EVALUATION_GATE,
            description="Evaluate facial similarity, prompt adherence, and aesthetic score against SLA",
            parameters={"thresholds": eval_metrics}
        ))
        step_idx += 1

        # Step 3: Saga Transactional Repair (Conditional Branch)
        if request.lifecycle_policy.allow_saga_repair and has_identity_anchor:
            target_thresh = request.requirements.quality_thresholds.face_similarity or 0.80
            steps.append(LogicalStep(
                step_id=f"step_{step_idx:02d}_saga_face_repair",
                operator_type=LogicalOperatorType.SAGA_REPAIR_PATCH,
                description="Targeted inpainting patch on face mask using reference identity embedding",
                required_anchors=[identity_anchors[0].id],
                is_conditional=True,
                condition_metric="face_similarity",
                condition_threshold=target_thresh,
                parameters={
                    "target_region": "face",
                    "denoising_strength": 0.35,
                    "max_attempts": request.lifecycle_policy.max_repair_passes
                }
            ))
            step_idx += 1

        # Step 4: Resolution Enhancement / Super-Resolution if dimensions exceed 1024
        req_dim = request.requirements.dimensions
        if req_dim.width > 1024 or req_dim.height > 1024:
            steps.append(LogicalStep(
                step_id=f"step_{step_idx:02d}_super_resolution",
                operator_type=LogicalOperatorType.POST_UPSCALE,
                description=f"Neural upscale canvas to final target resolution {req_dim.width}x{req_dim.height}",
                parameters={
                    "target_width": req_dim.width,
                    "target_height": req_dim.height
                }
            ))
            step_idx += 1

        return LogicalPlan(
            plan_id=f"plan_{request.request_id}",
            request_id=request.request_id,
            steps=steps
        )
