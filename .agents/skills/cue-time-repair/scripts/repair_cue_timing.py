#!/usr/bin/env python3
"""
CLI tool to diagnose and repair cue timestamps in SceneFlow cue files.
Fixes LLM colon-stripping anomalies (e.g., 102.0 for 1:02 -> 62.0s).
"""

import argparse
import json
import sys
from pathlib import Path


def diagnose_and_fix_timestamp(t: float) -> tuple[float, bool]:
    """Converts MMSS decimal hallucination into true elapsed seconds."""
    if t >= 100:
        minutes = int(t // 100)
        seconds = t - (minutes * 100)
        if seconds < 60:
            fixed = round(minutes * 60 + seconds, 2)
            return fixed, True
    return round(t, 2), False


def process_cues(input_path: Path, output_path: Path, in_place: bool = False):
    if not input_path.exists():
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cues = data.get("cues", [])
    if not cues:
        print("Warning: No 'cues' array found in JSON.", file=sys.stderr)
        return

    fixed_count = 0
    inversions = []

    for cue in cues:
        s, s_fixed = diagnose_and_fix_timestamp(cue.get("startTime", 0.0))
        e, e_fixed = diagnose_and_fix_timestamp(cue.get("endTime", 0.0))

        if s_fixed or e_fixed:
            fixed_count += 1

        cue["startTime"] = s
        cue["endTime"] = e

        if s > e:
            inversions.append((cue.get("id"), s, e))

    target_path = input_path if in_place else output_path

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"Diagnosed {len(cues)} cues:")
    print(f" - Fixed MMSS timestamps: {fixed_count} cues")
    if inversions:
        print(f" - WARNING: {len(inversions)} cues have startTime > endTime: {inversions}")
    print(f"Output saved to: {target_path}")


def main():
    parser = argparse.ArgumentParser(description="Repair corrupted cue timestamps in Screenplay-Sync JSON.")
    parser.add_argument("input", help="Path to input cue JSON file")
    parser.add_argument("-o", "--output", help="Path to output cue JSON file")
    parser.add_argument("--in-place", action="store_true", help="Overwrite the input file directly")

    args = parser.parse_args()
    input_p = Path(args.input)
    output_p = Path(args.output) if args.output else input_p.with_name(f"{input_p.stem}_fixed{input_p.suffix}")

    process_cues(input_p, output_p, args.in_place)


if __name__ == "__main__":
    main()
