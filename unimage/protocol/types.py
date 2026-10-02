"""
Capability-based Declarative Media Protocol (CDMP) - Core Types
"""

from enum import Enum

class TaskType(str, Enum):
    TEXT_TO_IMAGE = "text_to_image"
    CHARACTER_CONSISTENT_EDIT = "character_consistent_edit"
    STYLE_TRANSFER = "style_transfer"
    INPAINT_REPAIR = "inpaint_repair"
    OUTPAINT_EXTEND = "outpaint_extend"
    IMAGE_TO_VIDEO = "image_to_video"

class AnchorType(str, Enum):
    IDENTITY = "identity"             # Facial / character feature embedding
    COMPOSITION = "composition"       # Depth, Canny edge, or pose guidance
    COLOR_PALETTE = "color_palette"   # Color scheme / grading anchor
    TYPOGRAPHY = "typography"         # Precise text rendering anchor

class FidelityLevel(str, Enum):
    RELAXED = "relaxed"   # ~0.65 threshold
    STANDARD = "standard" # ~0.78 threshold
    STRICT = "strict"     # ~0.88 threshold

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    SKIPPED = "skipped"

class RoutingStrategy(str, Enum):
    PARETO_OPTIMAL = "pareto_optimal" # Balance cost, latency, quality
    LOWEST_COST = "lowest_cost"
    LOWEST_LATENCY = "lowest_latency"
    MAX_QUALITY = "max_quality"
