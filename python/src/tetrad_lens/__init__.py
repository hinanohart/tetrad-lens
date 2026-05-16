"""tetrad-lens: McLuhan-tetrad-shaped attribute schema and three-tier tagger.

See README.md for project scope and non-goals.
"""

from tetrad_lens.heuristic import HeuristicTagger
from tetrad_lens.llm_tagger import LLMTagger
from tetrad_lens.review_queue import ReviewQueueClient
from tetrad_lens.schema import (
    TetradScore,
    TetradSpan,
    figure_ground_of,
)
from tetrad_lens.sdk import (
    install_processor,
    observe,
)

__version__ = "0.2.0"
SCHEMA_VERSION = "1.0.0"

__all__ = [
    "TetradScore",
    "TetradSpan",
    "figure_ground_of",
    "observe",
    "install_processor",
    "HeuristicTagger",
    "LLMTagger",
    "ReviewQueueClient",
    "__version__",
    "SCHEMA_VERSION",
]
