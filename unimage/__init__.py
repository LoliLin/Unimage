"""
Unimage: Next-Generation Capability-Based Generative Media Runtime Layer (CMRL)
"""

__version__ = "0.1.0-alpha"

from unimage.client import UnimageClient
from unimage.protocol.schema import (
    DeclarativeMediaRequest,
    MediaIntent,
    MediaAnchor,
    MediaRequirements,
    LifecyclePolicy,
    ExecutionResult,
    Dimensions,
    QualityThresholds
)
from unimage.protocol.types import (
    TaskType,
    AnchorType,
    FidelityLevel,
    StepStatus,
    RoutingStrategy
)

__all__ = [
    "UnimageClient",
    "DeclarativeMediaRequest",
    "MediaIntent",
    "MediaAnchor",
    "MediaRequirements",
    "LifecyclePolicy",
    "ExecutionResult",
    "Dimensions",
    "QualityThresholds",
    "TaskType",
    "AnchorType",
    "FidelityLevel",
    "StepStatus",
    "RoutingStrategy"
]
