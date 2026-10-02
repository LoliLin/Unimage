"""
Unimage Saga Execution Engine & Transactional Compensator
"""

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from unimage.protocol.types import StepStatus
from unimage.protocol.schema import (
    DeclarativeMediaRequest,
    ExecutionResult,
    StepTrace,
)
from unimage.compiler.optimizer import PhysicalExecutionPlan, PhysicalStep
from unimage.adapters.base import BaseModelAdapter, StepExecutionOutput
from unimage.adapters.mock_adapter import MockProviderAdapter
from unimage.evaluator.quality_checker import QualityEvaluator, global_evaluator
from unimage.runtime.state_store import StateStore, AssetState, global_state_store

class SagaExecutionEngine:
    """
    Stateful execution engine implementing Saga-style transaction boundaries
    and dynamic quality compensation for generative media workflows.
    """

    def __init__(
        self,
        default_adapter: Optional[BaseModelAdapter] = None,
        evaluator: Optional[QualityEvaluator] = None,
        state_store: Optional[StateStore] = None
    ):
        self.adapter = default_adapter or MockProviderAdapter(speedup_factor=5.0)
        self.evaluator = evaluator or global_evaluator
        self.state_store = state_store or global_state_store

    async def execute(
        self,
        plan: PhysicalExecutionPlan,
        request: DeclarativeMediaRequest
    ) -> ExecutionResult:
        traces: List[StepTrace] = []
        total_cost = 0.0
        start_wall_time = time.time()
        
        current_asset_uri: str = ""
        current_latent_ref: Optional[str] = None
        current_eval_metrics: Dict[str, float] = {}
        repaired_passes = 0
        sla_passed = True

        session_id = request.request_id

        for step in plan.physical_steps:
            step_start = time.time()
            
            # 1. Check if step is conditional (e.g. Saga Repair)
            if step.is_conditional:
                metric_name = step.condition_metric
                thresh = step.condition_threshold
                
                # Check whether current quality metric breaches the threshold
                current_val = current_eval_metrics.get(metric_name, 1.0)
                needs_repair = (thresh is not None) and (current_val < thresh)

                if not needs_repair:
                    # Condition not met -> Skip repair step, saving compute!
                    traces.append(StepTrace(
                        step_id=step.step_id,
                        operator_name=step.logical_operator,
                        provider=step.provider,
                        model=step.selected_model_id,
                        status=StepStatus.SKIPPED,
                        duration_ms=0,
                        cost_cents=0.0,
                        notes=f"Skipped: {metric_name} ({current_val:.2f}) already meets SLA threshold ({thresh:.2f})"
                    ))
                    continue
                else:
                    # Condition met: Trigger Saga Repair
                    repaired_passes += 1

            # 2. Handle Evaluation Gate
            if step.logical_operator == "evaluation_gate":
                current_eval_metrics = self.evaluator.evaluate_synthesis(
                    image_uri=current_asset_uri,
                    anchor_uri=request.anchors[0].source_uri if request.anchors else None,
                    is_after_repair=(repaired_passes > 0)
                )
                
                duration_ms = int((time.time() - step_start) * 1000)
                total_cost += step.estimated_cost_cents

                traces.append(StepTrace(
                    step_id=step.step_id,
                    operator_name=step.logical_operator,
                    provider=step.provider,
                    model=step.selected_model_id,
                    status=StepStatus.COMPLETED,
                    duration_ms=duration_ms,
                    cost_cents=step.estimated_cost_cents,
                    output_asset_uri=current_asset_uri,
                    intermediate_latent_ref=current_latent_ref,
                    evaluation_metrics=current_eval_metrics,
                    notes=f"Metrics: face_similarity={current_eval_metrics.get('face_similarity')}, aesthetic={current_eval_metrics.get('aesthetic_score')}"
                ))
                continue

            # 3. Execute generative/repair/upscale step via Adapter
            context = {
                "session_id": session_id,
                "current_asset_uri": current_asset_uri,
                "current_latent_ref": current_latent_ref,
                "anchors": request.anchors,
                "prompt": request.intent.prompt
            }

            output: StepExecutionOutput = await self.adapter.execute(step, context)
            
            current_asset_uri = output.output_asset_uri
            if output.intermediate_latent_ref:
                current_latent_ref = output.intermediate_latent_ref

            total_cost += output.actual_cost_cents

            # Save state in distributed cache
            self.state_store.put_asset(AssetState(
                asset_id=f"ast_{session_id}_{step.step_id}",
                session_id=session_id,
                step_id=step.step_id,
                image_uri=current_asset_uri,
                latent_tensor_ref=current_latent_ref
            ))

            # If this was a repair pass, re-evaluate metrics
            step_eval_metrics = {}
            if step.logical_operator == "saga_repair_patch":
                current_eval_metrics = self.evaluator.evaluate_synthesis(
                    image_uri=current_asset_uri,
                    anchor_uri=request.anchors[0].source_uri if request.anchors else None,
                    is_after_repair=True
                )
                step_eval_metrics = current_eval_metrics

            traces.append(StepTrace(
                step_id=step.step_id,
                operator_name=step.logical_operator,
                provider=step.provider,
                model=step.selected_model_id,
                status=output.status,
                duration_ms=output.actual_latency_ms,
                cost_cents=output.actual_cost_cents,
                output_asset_uri=output.output_asset_uri,
                intermediate_latent_ref=output.intermediate_latent_ref,
                evaluation_metrics=step_eval_metrics,
                notes=output.notes
            ))

        total_wall_ms = int((time.time() - start_wall_time) * 1000)

        # Check final SLA status
        face_thresh = request.requirements.quality_thresholds.face_similarity
        if face_thresh is not None:
            final_sim = current_eval_metrics.get("face_similarity", 1.0)
            if final_sim < face_thresh:
                sla_passed = False

        return ExecutionResult(
            request_id=request.request_id,
            final_asset_uri=current_asset_uri,
            status=StepStatus.COMPLETED if sla_passed else StepStatus.FAILED,
            total_latency_ms=total_wall_ms,
            total_cost_cents=round(total_cost, 2),
            repaired_passes=repaired_passes,
            sla_passed=sla_passed,
            evaluation_summary=current_eval_metrics,
            execution_trace=traces,
            session_latent_key=current_latent_ref
        )
