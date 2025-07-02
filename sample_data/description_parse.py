
"""
sample_lines.py

Randomly sample N lines from a text file and write them to an output file.
Keeps the sampled lines in their original order.

Usage
-----
python description_parse.py input_file.txt output_file.txt --n 382  --seed 42
"""
import argparse
import random
import sys
from pathlib import Path

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Randomly sample N lines from a text file."
    )
    p.add_argument("input_file", type=Path, help="Path to the source file")
    p.add_argument("output_file", type=Path, help="Path to write the sample")
    p.add_argument("-n", "--num-lines", type=int, default=382,
                   help="Number of lines to sample (default: 382)")
    p.add_argument("--seed", type=int, default=None,
                   help="Random seed for reproducibility")
    return p.parse_args()

def main() -> None:
    args = parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Read all lines (thousands is small enough to fit in memory comfortably)
    try:
        with args.input_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        sys.exit(f"Error: {args.input_file} not found.")

    total = len(lines)
    if args.num_lines <= 0:
        sys.exit("Error: --num-lines must be positive.")
    if args.num_lines > total:
        sys.exit(f"Error: requested {args.num_lines} lines but file has only {total}.")

    # Choose indices to preserve original ordering
    sampled_indices = sorted(random.sample(range(total), args.num_lines))

    # Write the sampled lines
    with args.output_file.open("w", encoding="utf-8") as out:
        for idx in sampled_indices:
            out.write(lines[idx])

    print(
        f"✓ Wrote {args.num_lines} of {total} lines "
        f"from {args.input_file} → {args.output_file}"
    )

if __name__ == "__main__":
    main()
