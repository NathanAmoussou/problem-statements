"""
SPDX-FileCopyrightText: 2026 Nathan Amoussou <nathan.amoussou@etu.univ-cotedazur.fr>

SPDX-License-Identifier: Apache-2.0

Solution evaluator for the Quadratic Assignment Problem.

Reads an instance file and a solution file in the formats described in the
problem statement, recomputes the objective value of the solution, and checks
the validity conditions stated there:

  - the instance must contain exactly 2 n^2 matrix entries after n, none of
    them negative;
  - the problem size declared in the solution must match the instance;
  - the n values must form a permutation of {1, ..., n};
  - the declared objective value must equal the recomputed one.

Usage:

    python3 evaluation.py <instance file> <solution file>

Exits with status 0 if the solution is valid, and 1 otherwise. Note that
QAPLIB solution files do not always follow the format described in the problem
statement and may require normalisation before being read by this script.
"""

import argparse
import sys


class InvalidFile(Exception):
    """Raised when an instance or solution file does not follow the format."""


def read_integers(filename):
    """Return the whitespace-separated integers of a file, in order."""
    try:
        with open(filename, "r") as f:
            tokens = f.read().split()
    except OSError as e:
        raise InvalidFile("cannot read %s: %s" % (filename, e.strerror))

    values = []
    for token in tokens:
        try:
            values.append(int(token))
        except ValueError:
            raise InvalidFile("%s: expected an integer, found %r" % (filename, token))
    return values


def read_instance(filename):
    """Return the size n and the flow and distance matrices of an instance."""
    values = read_integers(filename)
    if not values:
        raise InvalidFile("%s: file is empty" % filename)

    n = values[0]
    if n <= 0:
        raise InvalidFile(
            "%s: the problem size must be positive, found %d" % (filename, n)
        )

    entries = values[1:]
    if len(entries) != 2 * n * n:
        raise InvalidFile(
            "%s: expected %d matrix entries after n = %d, found %d"
            % (filename, 2 * n * n, n, len(entries))
        )

    negative = [v for v in entries if v < 0]
    if negative:
        raise InvalidFile(
            "%s: matrix entries must be non-negative, found %d" % (filename, negative[0])
        )

    flow = [entries[i * n : (i + 1) * n] for i in range(n)]
    offset = n * n
    distance = [entries[offset + i * n : offset + (i + 1) * n] for i in range(n)]
    return n, flow, distance


def read_solution(filename, n):
    """Return the declared objective value and the permutation of a solution."""
    values = read_integers(filename)
    if len(values) != n + 2:
        raise InvalidFile(
            "%s: expected %d values (n, objective value, and %d locations), found %d"
            % (filename, n + 2, n, len(values))
        )

    declared_n, declared_value = values[0], values[1]
    if declared_n != n:
        raise InvalidFile(
            "%s: declared problem size %d does not match the instance size %d"
            % (filename, declared_n, n)
        )

    permutation = values[2:]
    if sorted(permutation) != list(range(1, n + 1)):
        raise InvalidFile(
            "%s: the %d values do not form a permutation of {1, ..., %d}"
            % (filename, n, n)
        )

    return declared_value, permutation


def objective_value(flow, distance, permutation):
    """Return the objective value of a permutation, with locations 1-indexed."""
    n = len(permutation)
    location = [p - 1 for p in permutation]
    return sum(
        flow[i][j] * distance[location[i]][location[j]]
        for i in range(n)
        for j in range(n)
    )


def main():
    parser = argparse.ArgumentParser(description="Evaluate a QAP solution.")
    parser.add_argument("instance", help="instance file")
    parser.add_argument("solution", help="solution file")
    args = parser.parse_args()

    try:
        n, flow, distance = read_instance(args.instance)
        declared_value, permutation = read_solution(args.solution, n)
    except InvalidFile as e:
        print("error: %s" % e, file=sys.stderr)
        return 1

    value = objective_value(flow, distance, permutation)
    if value != declared_value:
        print(
            "error: %s: declared objective value %d, recomputed %d"
            % (args.solution, declared_value, value),
            file=sys.stderr,
        )
        return 1

    print("valid solution of objective value %d" % value)
    return 0


if __name__ == "__main__":
    sys.exit(main())
