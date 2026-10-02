"""
Unit & Integration Tests for Unimage Media Runtime Layer
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unimage.protocol.schema import (
    DeclarativeMediaRequest,
    MediaIntent,
    MediaAnchor,
    MediaRequirements,
    LifecyclePolicy,
    Dimensions,
    QualityThresholds
)
from unimage.protocol.types import TaskType, AnchorType, FidelityLevel, StepStatus, RoutingStrategy
from unimage.compiler.planner import LogicalPlanner, LogicalOperatorType
from unimage.compiler.optimizer import PhysicalOptimizer
from unimage.client import UnimageClient
from unimage.evaluator.quality_checker import QualityEvaluator

def test_logical_planner_generates_repair_for_identity_anchor():
    planner = LogicalPlanner()
    req = DeclarativeMediaRequest(
        intent=MediaIntent(
            task=TaskType.CHARACTER_CONSISTENT_EDIT,
            action="scene_transfer",
            prompt="cyberpunk detective"
        ),
        anchors=[
            MediaAnchor(
                type=AnchorType.IDENTITY,
                source_uri="s3://test/face.png",
                fidelity=FidelityLevel.STRICT
            )
        ],
        requirements=MediaRequirements(
            dimensions=Dimensions(width=1920, height=1080),
            quality_thresholds=QualityThresholds(face_similarity=0.88)
        )
    )

    plan = planner.plan(req)
    op_types = [s.operator_type for s in plan.steps]
    
    assert LogicalOperatorType.BASE_SYNTHESIS in op_types
    assert LogicalOperatorType.EVALUATION_GATE in op_types
    assert LogicalOperatorType.SAGA_REPAIR_PATCH in op_types
    assert LogicalOperatorType.POST_UPSCALE in op_types

def test_physical_optimizer_budget_enforcement():
    planner = LogicalPlanner()
    optimizer = PhysicalOptimizer()
    
    req = DeclarativeMediaRequest(
        intent=MediaIntent(
            task=TaskType.TEXT_TO_IMAGE,
            action="generate",
            prompt="futuristic city"
        ),
        requirements=MediaRequirements(
            max_cost_cents=2.0,
            routing_strategy=RoutingStrategy.LOWEST_COST
        )
    )

    l_plan = planner.plan(req)
    p_plan = optimizer.optimize(l_plan, req)

    assert p_plan.total_estimated_cost_cents <= 2.0
    assert len(p_plan.physical_steps) >= 1

@pytest.mark.asyncio
async def test_saga_runtime_execution_pass():
    client = UnimageClient()
    req = DeclarativeMediaRequest(
        intent=MediaIntent(
            task=TaskType.CHARACTER_CONSISTENT_EDIT,
            action="scene_transfer",
            prompt="cyberpunk detective"
        ),
        anchors=[
            MediaAnchor(
                type=AnchorType.IDENTITY,
                source_uri="s3://test/face.png",
                fidelity=FidelityLevel.STANDARD
            )
        ],
        requirements=MediaRequirements(
            quality_thresholds=QualityThresholds(face_similarity=0.80)
        )
    )

    result = await client.dispatch(req)
    assert result.status == StepStatus.COMPLETED
    assert result.sla_passed is True
    assert result.final_asset_uri.startswith("https://cdn.unimage.dev/")
    assert len(result.execution_trace) >= 2

if __name__ == "__main__":
    asyncio.run(test_saga_runtime_execution_pass())
    test_logical_planner_generates_repair_for_identity_anchor()
    test_physical_optimizer_budget_enforcement()
    print("All Unimage core tests PASSED!")
