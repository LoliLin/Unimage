"""
High-Fidelity Mock & Simulation Adapter
"""

import asyncio
import time
import uuid
from typing import Dict, Any

from unimage.adapters.base import BaseModelAdapter, StepExecutionOutput
from unimage.compiler.optimizer import PhysicalStep
from unimage.protocol.types import StepStatus

class MockProviderAdapter(BaseModelAdapter):
    """
    Simulation adapter that models realistic execution timings, latent generation,
    and asset production for zero-cost testing and demonstrations.
    """

    def __init__(self, speedup_factor: float = 10.0):
        # speedup_factor=10 makes 4000ms take 400ms in simulation
        self.speedup_factor = speedup_factor

    async def execute(self, step: PhysicalStep, context: Dict[str, Any]) -> StepExecutionOutput:
        start_time = time.time()
        
        # Simulate realistic latency (scaled)
        sim_sleep = (step.estimated_latency_ms / 1000.0) / self.speedup_factor
        await asyncio.sleep(sim_sleep)
        
        elapsed_ms = int((time.time() - start_time) * 1000 * self.speedup_factor)
        asset_id = f"art_{uuid.uuid4().hex[:8]}"
        
        # Generate representative mock URLs
        if "synthesis" in step.logical_operator:
            output_uri = f"https://cdn.unimage.dev/renders/{asset_id}_base.png"
            latent_ref = f"latent://cache/{asset_id}_tensor.safetensors"
            notes = f"Generated base frame using {step.selected_model_id} via {step.provider}"
        elif "repair" in step.logical_operator:
            output_uri = f"https://cdn.unimage.dev/renders/{asset_id}_repaired_face.png"
            latent_ref = f"latent://cache/{asset_id}_inpaint_tensor.safetensors"
            notes = "Inpainted facial mask with PuLID identity anchor embedding"
        elif "upscale" in step.logical_operator:
            output_uri = f"https://cdn.unimage.dev/renders/{asset_id}_4k_upscaled.png"
            latent_ref = None
            notes = f"Upscaled canvas via {step.selected_model_id}"
        else:
            output_uri = f"https://cdn.unimage.dev/renders/{asset_id}.png"
            latent_ref = None
            notes = "Processed step"

        return StepExecutionOutput(
            step_id=step.step_id,
            status=StepStatus.COMPLETED,
            output_asset_uri=output_uri,
            intermediate_latent_ref=latent_ref,
            actual_latency_ms=elapsed_ms,
            actual_cost_cents=step.estimated_cost_cents,
            notes=notes
        )
