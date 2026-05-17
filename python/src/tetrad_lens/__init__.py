"""tetrad-lens: McLuhan-tetrad-shaped attribute schema and three-tier tagger.

See README.md for project scope and non-goals.
"""

from tetrad_lens.heuristic import HeuristicTagger, tag_heuristically, token_count
from tetrad_lens.llm_tagger import LLMTagger
from tetrad_lens.masking import mask_data, mask_text
from tetrad_lens.review_queue import ReviewQueueClient
from tetrad_lens.schema import (
    EngelbartLevel,
    FigureGround,
    RoleSplit,
    TetradScore,
    TetradSpan,
    Tier,
    figure_ground_of,
)
from tetrad_lens.sdk import (
    install_processor,
    observe,
    tag_current_span,
    tetrad_context,
)

__version__ = "0.1.1"
SCHEMA_VERSION = "1.0.0"

__all__ = [
    # schema models
    "TetradScore",
    "TetradSpan",
    "RoleSplit",
    "FigureGround",
    "Tier",
    "EngelbartLevel",
    "figure_ground_of",
    # SDK entry points
    "observe",
    "install_processor",
    "tag_current_span",
    "tetrad_context",
    # taggers
    "HeuristicTagger",
    "tag_heuristically",
    "token_count",
    "LLMTagger",
    "ReviewQueueClient",
    # masking
    "mask_text",
    "mask_data",
    # versions
    "__version__",
    "SCHEMA_VERSION",
]
