"""Minimal CLI.

Usage::

    tetrad-lens --version
    tetrad-lens tag --text "an LLM agent that..."
    echo "..." | tetrad-lens tag
    tetrad-lens tag --text "..." --llm     # Tier 2 (requires Ollama)
"""

from __future__ import annotations

import argparse
import json
import sys

from tetrad_lens import SCHEMA_VERSION, __version__
from tetrad_lens.heuristic import tag_heuristically
from tetrad_lens.llm_tagger import LLMTagger
from tetrad_lens.masking import mask_text


def _read_text(args: argparse.Namespace) -> str | None:
    """Resolve the text input from --text or stdin (when piped)."""
    text_arg = args.text
    if text_arg is not None:
        return str(text_arg)
    if not sys.stdin.isatty():
        data = sys.stdin.read()
        return data if data else None
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tetrad-lens")
    parser.add_argument("--version", action="store_true", help="print version + schema version")
    sub = parser.add_subparsers(dest="cmd")

    p_tag = sub.add_parser("tag", help="run the tagger on a text snippet")
    p_tag.add_argument(
        "--text",
        help="text to tag (omit to read from stdin when piped)",
    )
    p_tag.add_argument(
        "--llm",
        action="store_true",
        help="use the LLM-assisted tagger (Tier 2; requires Ollama)",
    )
    p_tag.add_argument(
        "--no-mask",
        action="store_true",
        help="skip PII masking on the input (default: mask)",
    )
    p_tag.add_argument(
        "--pretty",
        action="store_true",
        help="pretty-print the JSON output (default: pretty when stdout is a TTY)",
    )

    args = parser.parse_args(argv)

    if args.version:
        print(f"tetrad-lens {__version__} (schema {SCHEMA_VERSION})")
        return 0

    if args.cmd == "tag":
        text = _read_text(args)
        if text is None:
            sys.stderr.write("tetrad-lens tag: provide --text or pipe input on stdin.\n")
            return 2

        if not args.no_mask:
            text = mask_text(text)

        if args.llm:
            span = LLMTagger().tag(text)
            if span is None:
                sys.stderr.write(
                    "LLM tagger returned no result (Ollama unreachable?); "
                    "falling back to heuristic.\n"
                )
                span = tag_heuristically(text)
        else:
            span = tag_heuristically(text)

        pretty = args.pretty or sys.stdout.isatty()
        json.dump(
            span.to_otel_attributes(),
            sys.stdout,
            indent=2 if pretty else None,
            ensure_ascii=False,
        )
        sys.stdout.write("\n")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
