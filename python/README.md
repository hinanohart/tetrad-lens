# tetrad-lens (Python)

Python package source for the `tetrad-lens` project. See the [repository root README](../README.md) for project overview, scope, and acknowledgements.

## Install

```bash
pip install "tetrad-lens"            # core
pip install "tetrad-lens[mcp]"       # + Cline / Claude Code MCP adapter
pip install "tetrad-lens[ollama]"    # + LLM-assisted (Tier 2) tagger
pip install "tetrad-lens[dev]"       # + test / lint / type-check
```

## Layout

```
python/
├── pyproject.toml
├── src/tetrad_lens/
│   ├── __init__.py
│   ├── schema.py            # Pydantic models mirroring schema/tetrad-v1.json
│   ├── sdk.py               # @observe + install_processor + tag_current_span
│   ├── masking.py           # PII masking (default ON)
│   ├── heuristic.py         # Tier 1
│   ├── llm_tagger.py        # Tier 2 (Ollama + position-swap)
│   ├── review_queue.py      # Tier 3 (Langfuse Score API)
│   ├── cli.py               # `tetrad-lens tag --text "..."`
│   └── adapters/
│       ├── cline_mcp.py
│       └── claude_code_skill.py
└── tests/
    ├── test_schema.py
    ├── test_heuristic.py
    ├── test_masking.py
    ├── test_review_queue.py
    ├── test_sdk_smoke.py
    └── test_cli.py
```

## Dev

```bash
cd python
pip install -e ".[dev]"
pytest -q
ruff check src tests
mypy src
```
