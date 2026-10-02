"""
Unimage Multi-Provider Adapter Dispatcher
"""

from typing import Dict, Optional, Any
from unimage.adapters.base import BaseModelAdapter, StepExecutionOutput
from unimage.adapters.mock_adapter import MockProviderAdapter
from unimage.adapters.fal_adapter import FalProviderAdapter
from unimage.adapters.openai_adapter import OpenAIProviderAdapter
from unimage.adapters.gemini_adapter import GeminiProviderAdapter
from unimage.adapters.comfy_adapter import ComfyUIAdapter
from unimage.compiler.optimizer import PhysicalStep

class AdapterDispatcher(BaseModelAdapter):
    """
    Intelligent dispatch bus routing physical steps to the appropriate provider adapter.
    """

    def __init__(self, force_mock: bool = False):
        self.force_mock = force_mock
        self._adapters: Dict[str, BaseModelAdapter] = {
            "fal.ai": FalProviderAdapter(),
            "openai": OpenAIProviderAdapter(),
            "google": GeminiProviderAdapter(),
            "comfy_cluster": ComfyUIAdapter(),
            "mock": MockProviderAdapter(speedup_factor=5.0)
        }
        self.default_mock = MockProviderAdapter(speedup_factor=5.0)

    def register_adapter(self, provider_name: str, adapter: BaseModelAdapter):
        self._adapters[provider_name] = adapter

    def get_adapter(self, provider_name: str) -> BaseModelAdapter:
        if self.force_mock:
            return self.default_mock
        return self._adapters.get(provider_name, self.default_mock)

    async def execute(self, step: PhysicalStep, context: Dict[str, Any]) -> StepExecutionOutput:
        adapter = self.get_adapter(step.provider)
        return await adapter.execute(step, context)
