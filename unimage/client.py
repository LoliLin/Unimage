"""
Unimage High-Level Client & Runtime Orchestrator
"""

from typing import Optional
from unimage.protocol.schema import DeclarativeMediaRequest, ExecutionResult
from unimage.compiler.planner import LogicalPlanner
from unimage.compiler.optimizer import PhysicalOptimizer
from unimage.runtime.saga_compensator import SagaExecutionEngine
from unimage.registry.capability_matrix import CapabilityRegistry, global_registry
from unimage.adapters.base import BaseModelAdapter
from unimage.adapters.dispatcher import AdapterDispatcher

class UnimageClient:
    """
    Main entry point for AI Agents and Applications calling the Unimage Runtime.
    """

    def __init__(
        self,
        registry: Optional[CapabilityRegistry] = None,
        adapter: Optional[BaseModelAdapter] = None
    ):
        self.registry = registry or global_registry
        self.planner = LogicalPlanner()
        self.optimizer = PhysicalOptimizer(self.registry)
        self.dispatcher = adapter or AdapterDispatcher()
        self.engine = SagaExecutionEngine(default_adapter=self.dispatcher)

    async def dispatch(self, request: DeclarativeMediaRequest) -> ExecutionResult:
        """
        End-to-End Orchestration:
        1. Compile Declarative Intent -> Logical Plan
        2. Optimize & Solve -> Physical Execution DAG
        3. Execute with Saga Transactional State & Quality Recovery
        """
        # Step 1: Logical Planning
        logical_plan = self.planner.plan(request)
        
        # Step 2: Physical Optimization
        physical_plan = self.optimizer.optimize(logical_plan, request)
        
        # Step 3: Saga Runtime Execution
        result = await self.engine.execute(physical_plan, request)
        return result
