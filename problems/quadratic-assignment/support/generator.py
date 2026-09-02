"""
SPDX-FileCopyrightText: 2026 Nathan Amoussou <nathan.amoussou@etu.univ-cotedazur.fr>

SPDX-License-Identifier: Apache-2.0

Instance generator for the Quadratic Assignment Problem.

Draws a flow matrix and a distance matrix uniformly at random and writes them
in the instance format described in the problem statement. Neither matrix is
constrained to be symmetric, since the entries are drawn independently.

Usage:

    python3 generator.py <n> [options]

where n, the only mandatory argument, is the number of facilities and
locations. The options are:

  --flow-range MIN MAX      bounds of the flow entries, 0 9 by default
  --distance-range MIN MAX  bounds of the distance entries, 0 9 by default
  --zero-diagonal           set both diagonals to zero, following the
                            convention of the example instance of the problem
                            statement; otherwise they are drawn like any other
                            entry, and may be zero
  --seed SEED               seed of the random number generator
  -o FILE, --output FILE    write to FILE instead of the standard output

The instance is written to the standard output unless --output is given, so it
can be piped or redirected. A run is fully determined by the problem size, the
ranges, the diagonal mode and the seed; when no seed is given, one is drawn and
reported on the standard error, so that any instance remains reproducible.

Note that drawing both matrices uniformly produces an unstructured instance,
which is adequate to exercise a parser or an objective function, but is not
representative of the instances found in practice.
"""

import argparse
import random
import sys


def generate(n, rng, flow_range, distance_range, zero_diagonal):
    """Return a flow matrix and a distance matrix of order n drawn with rng."""
    flow = [[rng.randint(*flow_range) for _ in range(n)] for _ in range(n)]
    distance = [[rng.randint(*distance_range) for _ in range(n)] for _ in range(n)]

    if zero_diagonal:
        for i in range(n):
            flow[i][i] = 0
            distance[i][i] = 0

    return flow, distance


def format_instance(n, flow, distance):
    """Return the instance in the format described in the problem statement."""
    rows = lambda matrix: "\n".join(" ".join(str(v) for v in row) for row in matrix)
    return "%d\n\n%s\n\n%s\n" % (n, rows(flow), rows(distance))


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a QAP instance.")
    parser.add_argument("size", type=int, help="number of facilities and locations")
    parser.add_argument(
        "--flow-range",
        type=int,
        nargs=2,
        metavar=("MIN", "MAX"),
        default=(0, 9),
        help="range of the flow entries (default: 0 9)",
    )
    parser.add_argument(
        "--distance-range",
        type=int,
        nargs=2,
        metavar=("MIN", "MAX"),
        default=(0, 9),
        help="range of the distance entries (default: 0 9)",
    )
    parser.add_argument(
        "--zero-diagonal",
        action="store_true",
        help="set both diagonals to zero instead of drawing them like any other entry",
    )
    parser.add_argument("--seed", type=int, help="seed of the random number generator")
    parser.add_argument(
        "-o", "--output", metavar="FILE", help="write to FILE instead of stdout"
    )
    args = parser.parse_args()

    if args.size <= 0:
        parser.error("the problem size must be positive, found %d" % args.size)
    for name in ("flow_range", "distance_range"):
        low, high = getattr(args, name)
        option = "--" + name.replace("_", "-")
        if low < 0:
            parser.error(
                "%s: the entries must be non-negative, found %d" % (option, low)
            )
        if low > high:
            parser.error("%s: %d is greater than %d" % (option, low, high))

    return args


def main():
    args = parse_args()

    seed = args.seed
    if seed is None:
        seed = random.randrange(2**32)
        print("seed: %d" % seed, file=sys.stderr)

    flow, distance = generate(
        args.size,
        random.Random(seed),
        args.flow_range,
        args.distance_range,
        args.zero_diagonal,
    )
    text = format_instance(args.size, flow, distance)

    if args.output is None:
        sys.stdout.write(text)
    else:
        try:
            with open(args.output, "w") as f:
                f.write(text)
        except OSError as e:
            print(
                "error: cannot write %s: %s" % (args.output, e.strerror),
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
