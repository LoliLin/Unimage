"""
Tests for Ingress (OpenAI Polyfill) and Egress (Provider Adapters) Compatibility Layers
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import asyncio
from fastapi.testclient import TestClient

from unimage.api.server import app
from unimage.adapters.dispatcher import AdapterDispatcher
from unimage.adapters.openai_adapter import OpenAIProviderAdapter
from unimage.adapters.gemini_adapter import GeminiProviderAdapter
from unimage.adapters.fal_adapter import FalProviderAdapter
from unimage.adapters.comfy_adapter import ComfyUIAdapter
from unimage.compiler.optimizer import PhysicalStep

client = TestClient(app)

def test_openai_ingress_image_generation():
    """Test standard OpenAI POST /v1/images/generations request"""
    payload = {
        "prompt": "Cyberpunk street with holographic banners",
        "model": "dall-e-3",
        "size": "1024x1024",
        "quality": "standard"
    }

    response = client.post("/v1/images/generations", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify standard OpenAI schema
    assert "created" in data
    assert "data" in data
    assert len(data["data"]) == 1
    assert data["data"][0]["url"].startswith("http")
    
    # Verify Unimage execution metadata is transparently attached
    assert "unimage_meta" in data
    assert data["unimage_meta"]["sla_passed"] is True

def test_openai_ingress_image_edits():
    """Test standard OpenAI POST /v1/images/edits request with face anchor"""
    payload = {
        "image": "https://cdn.example.com/character_face.png",
        "prompt": "Change background to neon city but keep the face identical",
        "size": "1024x1024"
    }

    response = client.post("/v1/images/edits", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"][0]["url"].startswith("http")
    assert "unimage_meta" in data

@pytest.mark.asyncio
async def test_egress_dispatcher_routing():
    """Test that AdapterDispatcher correctly instantiates and dispatches to registered providers"""
    dispatcher = AdapterDispatcher()

    # 1. Test OpenAI dispatch
    step_openai = PhysicalStep(
        step_id="test_openai",
        logical_operator="base_synthesis",
        selected_model_id="openai/dall-e-3",
        provider="openai",
        description="OpenAI test",
        estimated_cost_cents=4.0,
        estimated_latency_ms=100
    )
    res_openai = await dispatcher.execute(step_openai, {"prompt": "test"})
    assert res_openai.status.value == "completed"

    # 2. Test Google Gemini dispatch
    step_gemini = PhysicalStep(
        step_id="test_gemini",
        logical_operator="base_synthesis",
        selected_model_id="google/imagen-3",
        provider="google",
        description="Gemini test",
        estimated_cost_cents=3.0,
        estimated_latency_ms=100
    )
    res_gemini = await dispatcher.execute(step_gemini, {"prompt": "test"})
    assert res_gemini.status.value == "completed"

    # 3. Test Fal.ai dispatch
    step_fal = PhysicalStep(
        step_id="test_fal",
        logical_operator="base_synthesis",
        selected_model_id="fal/flux-schnell",
        provider="fal.ai",
        description="Fal test",
        estimated_cost_cents=0.35,
        estimated_latency_ms=100
    )
    res_fal = await dispatcher.execute(step_fal, {"prompt": "test"})
    assert res_fal.status.value == "completed"

    # 4. Test ComfyUI dispatch
    step_comfy = PhysicalStep(
        step_id="test_comfy",
        logical_operator="saga_repair_patch",
        selected_model_id="comfy/face-detailer-inpaint",
        provider="comfy_cluster",
        description="Comfy test",
        estimated_cost_cents=0.6,
        estimated_latency_ms=100
    )
    res_comfy = await dispatcher.execute(step_comfy, {"prompt": "test"})
    assert res_comfy.status.value == "completed"

if __name__ == "__main__":
    test_openai_ingress_image_generation()
    test_openai_ingress_image_edits()
    asyncio.run(test_egress_dispatcher_routing())
    print("All Ingress & Egress Compatibility Tests PASSED!")
