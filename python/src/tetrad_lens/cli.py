"""Minimal CLI: `tetrad-lens tag --text "..."` and `tetrad-lens version`."""

from __future__ import annotations

import argparse
import json
import sys

from tetrad_lens import SCHEMA_VERSION, __version__
from tetrad_lens.heuristic import tag_heuristically


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tetrad-lens")
    parser.add_argument("--version", action="store_true", help="print version + schema version")
    sub = parser.add_subparsers(dest="cmd")

    p_tag = sub.add_parser("tag", help="run the heuristic tagger on a text snippet")
    p_tag.add_argument("--text", required=True, help="text to tag")

    args = parser.parse_args(argv)

    if args.version:
        print(f"tetrad-lens {__version__} (schema {SCHEMA_VERSION})")
        return 0

    if args.cmd == "tag":
        span = tag_heuristically(args.text)
        json.dump(span.to_otel_attributes(), sys.stdout, indent=2, ensure_ascii=False)
        print()
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
