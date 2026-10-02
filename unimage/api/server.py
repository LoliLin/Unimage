"""
Unimage API Gateway & Fast Ingress Server
"""

from fastapi import FastAPI, HTTPException
from unimage.protocol.schema import DeclarativeMediaRequest, ExecutionResult
from unimage.registry.capability_matrix import global_registry
from unimage.client import UnimageClient
from unimage.api.openai_compat import router as openai_compat_router

app = FastAPI(
    title="Unimage: Generative Media Runtime Layer",
    version="0.1.0",
    description="Capability-based Media API Gateway & Execution Runtime"
)

# Mount OpenAI Compatibility Polyfill
app.include_router(openai_compat_router)

client = UnimageClient()

@app.get("/v1/media/health")
async def health_check():
    return {"status": "healthy", "engine": "unimage-cmrl", "version": "0.1.0"}

@app.get("/v1/media/capabilities")
async def list_capabilities():
    """List multidimensional capability vectors for registered models"""
    return global_registry.list_all()

@app.post("/v1/media/intent", response_model=ExecutionResult)
async def dispatch_media_intent(request: DeclarativeMediaRequest):
    """
    Primary CDMP Ingress:
    Submits a declarative intent, anchors, and SLA constraints.
    Returns compiled execution trace, evaluated quality, and delivered asset.
    """
    try:
        result = await client.dispatch(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
