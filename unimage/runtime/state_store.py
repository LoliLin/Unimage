"""
Unimage Distributed Latent & State Cache
"""

import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class AssetState(BaseModel):
    asset_id: str
    session_id: str
    step_id: str
    image_uri: str
    latent_tensor_ref: Optional[str] = None
    mask_uri: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)

class StateStore:
    """
    In-memory / Redis / S3 backed cache for intermediate assets and latent vectors.
    Solves the 'Pixel Round-trip' problem: retains latents and attention maps across steps.
    """

    def __init__(self):
        self._assets: Dict[str, AssetState] = {}
        self._session_index: Dict[str, list] = {}

    def put_asset(self, asset: AssetState):
        self._assets[asset.asset_id] = asset
        if asset.session_id not in self._session_index:
            self._session_index[asset.session_id] = []
        self._session_index[asset.session_id].append(asset.asset_id)

    def get_asset(self, asset_id: str) -> Optional[AssetState]:
        return self._assets.get(asset_id)

    def get_latest_session_asset(self, session_id: str) -> Optional[AssetState]:
        asset_ids = self._session_index.get(session_id, [])
        if not asset_ids:
            return None
        return self._assets.get(asset_ids[-1])

global_state_store = StateStore()
