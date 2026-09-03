#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: © 2026 Nathan Amoussou <nathan.amoussou@etu.univ-cotedazur.fr>
#
# SPDX-License-Identifier: Apache-2.0

"""
ROAR-NET API model of the Quadratic Assignment Problem.

The problem is described in the README of the parent folder. An instance is
given by a size n and two non-negative integer n x n matrices, a flow matrix F
between facilities and a distance matrix D between locations. A solution is a
permutation pi, where pi(i) is the location assigned to facility i, and its
objective value is

    sum_i sum_j F[i][j] * D[pi(i)][pi(j)]

which is to be minimised. Every permutation is feasible.

Permutations are represented as lists of locations indexed by facility, and
both facilities and locations are numbered from 0 here, whereas the instance
and solution file formats number locations from 1.
"""

from __future__ import annotations

import logging
import math
import random
import sys
from collections.abc import Iterable, Sequence
from logging import getLogger
from typing import Self, TextIO, final

from roar_net_api.operations import (
    SupportsApplyMove,
    SupportsCopySolution,
    SupportsLocalNeighbourhood,
    SupportsMoves,
    SupportsObjectiveValue,
    SupportsObjectiveValueIncrement,
    SupportsRandomMove,
    SupportsRandomMovesWithoutReplacement,
    SupportsRandomSolution,
)

log = getLogger(__name__)

# ---------------------------------- Helpers ---------------------------------


def sparse_fisher_yates_iter(n: int) -> Iterable[int]:
    """
    Sparse Fisher-Yates sampler, yielding a random permutation of 0, ..., n-1
    one value at a time. See <https://doi.org/10.48550/arXiv.2104.05091>.
    """
    p: dict[int, int] = dict()
    for i in range(n - 1, -1, -1):
        r = random.randrange(i + 1)
        yield p.get(r, r)
        if i != r:
            p[r] = p.get(i, i)


def unordered_pair(x: int) -> tuple[int, int]:
    """
    Return the pair (r, s) with r < s that the non-negative integer x indexes,
    pairs being enumerated as (0,1), (0,2), (1,2), (0,3), (1,3), (2,3), ...

    This maps 0, ..., n(n-1)/2 - 1 onto the pairs of facilities of a problem of
    size n, so that sampling pairs amounts to sampling integers. The inversion
    follows the one commented in the tsp example of roar-net-api-py, which
    needs offsets and a special case because not every pair is a valid 2-opt
    move, whereas every pair of facilities is a valid swap here.
    """
    s = (1 + math.isqrt(1 + 8 * x)) // 2
    return x - s * (s - 1) // 2, s


# --------------------------------- Solution ---------------------------------


@final
class Solution(SupportsCopySolution, SupportsObjectiveValue):
    def __init__(self, problem: Problem, permutation: list[int], objective: int):
        self.problem = problem
        # permutation[i] is the location assigned to facility i, from 0
        self.permutation = permutation
        # Kept up to date by apply_move, never recomputed
        self.objective = objective

    def __str__(self) -> str:
        return " ".join(str(location + 1) for location in self.permutation)

    def to_textio(self, f: TextIO) -> None:
        """
        Write the solution to a text I/O destination `f` in the format of the
        problem statement, where locations are numbered from 1.
        """
        f.write(f"{self.problem.n} {self.objective}\n{self}\n")

    def copy_solution(self) -> Self:
        return self.__class__(self.problem, self.permutation.copy(), self.objective)

    def objective_value(self) -> int:
        """
        Return the objective value of the solution, which is held rather than
        computed. Every permutation is feasible, so it is never undefined.
        """
        return self.objective


# ----------------------------------- Move -----------------------------------


@final
class SwapMove(
    SupportsApplyMove[Solution],
    SupportsObjectiveValueIncrement[Solution],
):
    def __init__(self, neighbourhood: SwapNeighbourhood, r: int, s: int):
        # The neighbourhood that created the move is not used here, since the
        # instance data is reached through the solution, but it is kept for
        # consistency with the other models and because a move that has to
        # build another one, such as its inverse, needs one to pass on.
        self.neighbourhood = neighbourhood
        # r and s are facilities, whose locations are to be exchanged
        self.r = r
        self.s = s

    def __str__(self) -> str:
        return f"Move: exchange the locations of facilities {self.r} and {self.s}"

    def objective_value_increment(self, solution: Solution) -> int:
        """
        Return the variation of the objective value that applying the move
        would cause, without modifying the solution.

        Exchanging the locations of two facilities leaves every other pi(k)
        unchanged, so only the terms of the objective function whose row or
        column is r or s are affected. There are O(n) of them, against the
        O(n^2) terms of a full evaluation.
        """
        problem = solution.problem
        f, d, n = problem.flow, problem.distance, problem.n
        pi, r, s = solution.permutation, self.r, self.s
        a, b = pi[r], pi[s]

        increment = 0
        for k in range(n):
            if k == r or k == s:
                continue
            c = pi[k]
            increment += f[r][k] * (d[b][c] - d[a][c]) + f[k][r] * (d[c][b] - d[c][a])
            increment += f[s][k] * (d[a][c] - d[b][c]) + f[k][s] * (d[c][a] - d[c][b])

        # The four terms that involve r and s only, and no other facility.
        # The first two are the diagonal ones, which vanish when the diagonals
        # of both matrices are zero, and the last two are those of the pair
        # being exchanged.
        increment += f[r][r] * (d[b][b] - d[a][a]) + f[s][s] * (d[a][a] - d[b][b])
        increment += f[r][s] * (d[b][a] - d[a][b]) + f[s][r] * (d[a][b] - d[b][a])
        return increment

    def apply_move(self, solution: Solution) -> Solution:
        """
        Exchange the locations of the two facilities in place, and update the
        objective value held by the solution.

        The increment is computed before the exchange, since it is expressed
        in terms of the current permutation, and it is obtained from
        objective_value_increment rather than recomputed here, so that the two
        cannot disagree.
        """
        solution.objective += self.objective_value_increment(solution)
        pi, r, s = solution.permutation, self.r, self.s
        pi[r], pi[s] = pi[s], pi[r]
        return solution


# ------------------------------- Neighbourhood ------------------------------


@final
class SwapNeighbourhood(
    SupportsMoves[Solution, SwapMove],
    SupportsRandomMovesWithoutReplacement[Solution, SwapMove],
    SupportsRandomMove[Solution, SwapMove],
):
    """
    The neighbourhood in which the neighbours of a solution are the
    permutations obtained by exchanging the locations of two facilities.

    A solution of size n has n(n-1)/2 neighbours. This neighbourhood induces
    the Cayley distance on permutations, that is, the least number of
    transpositions needed to turn one into the other.
    """

    def __init__(self, problem: Problem):
        self.problem = problem

    def moves(self, solution: Solution) -> Iterable[SwapMove]:
        """Yield every move of the neighbourhood, in a fixed order."""
        assert self.problem is solution.problem
        for s in range(1, self.problem.n):
            for r in range(s):
                yield SwapMove(self, r, s)

    def random_moves_without_replacement(
        self, solution: Solution
    ) -> Iterable[SwapMove]:
        """
        Yield every move of the neighbourhood exactly once, in a uniformly
        random order, one at a time.

        Pairs are drawn by sampling their index, so that no list of moves is
        ever built and stopping early costs only what has been consumed.
        """
        assert self.problem is solution.problem
        n = self.problem.n
        for x in sparse_fisher_yates_iter(n * (n - 1) // 2):
            r, s = unordered_pair(x)
            yield SwapMove(self, r, s)

    def random_move(self, solution: Solution) -> SwapMove | None:
        """
        Return a move drawn uniformly at random, or None when the problem is
        too small for the neighbourhood to contain any.
        """
        assert self.problem is solution.problem
        n = self.problem.n
        if n < 2:
            return None
        r, s = unordered_pair(random.randrange(n * (n - 1) // 2))
        return SwapMove(self, r, s)


# --------------------------------- Problem ----------------------------------


@final
class Problem(
    SupportsLocalNeighbourhood[SwapNeighbourhood],
    SupportsRandomSolution[Solution],
):
    def __init__(
        self,
        flow: Sequence[Sequence[int]],
        distance: Sequence[Sequence[int]],
        name: str = "unnamed",
    ):
        self.flow = tuple(tuple(row) for row in flow)
        self.distance = tuple(tuple(row) for row in distance)
        self.name = name
        self.n = len(self.flow)
        self.l_nbhood: SwapNeighbourhood | None = None

    def __str__(self) -> str:
        rows = lambda matrix: "\n".join(" ".join(map(str, row)) for row in matrix)
        return f"{self.n}\n\n{rows(self.flow)}\n\n{rows(self.distance)}"

    def evaluate(self, permutation: Sequence[int]) -> int:
        """
        Return the objective value of a permutation, computed from scratch.

        This is the O(n^2) evaluation. Local search relies on the O(n)
        increment of a swap instead, and only needs this one to evaluate an
        initial solution.
        """
        f, d, n = self.flow, self.distance, self.n
        return sum(
            f[i][j] * d[permutation[i]][permutation[j]]
            for i in range(n)
            for j in range(n)
        )

    def local_neighbourhood(self) -> SwapNeighbourhood:
        """
        Return the neighbourhood in which two solutions are neighbours when
        one is obtained from the other by swapping the locations of two
        facilities.

        The neighbourhood defines how to move. It holds no state of its own and
        is built on first request, so that all the algorithms run on a problem
        share a single instance of it.
        """
        if self.l_nbhood is None:
            self.l_nbhood = SwapNeighbourhood(self)
        return self.l_nbhood

    def random_solution(self) -> Solution:
        """
        Return a solution drawn uniformly at random, to be used as a starting
        point. Every permutation is feasible, so shuffling is enough.

        This is the only place where the objective value is computed from
        scratch, since the solution it returns has no predecessor to derive it
        from.
        """
        permutation = list(range(self.n))
        random.shuffle(permutation)
        return Solution(self, permutation, self.evaluate(permutation))

    @classmethod
    def from_textio(cls, f: TextIO, name: str = "unnamed") -> Self:
        """
        Create a problem from a text I/O source `f` in the format of the
        problem statement, that is, n followed by the n^2 entries of the flow
        matrix and the n^2 entries of the distance matrix, both in row-major
        order and separated by any whitespace.
        """
        values = list(map(int, f.read().split()))
        if not values:
            raise ValueError("Invalid instance: no data")

        n, entries = values[0], values[1:]
        if n <= 0:
            raise ValueError(
                f"Invalid instance: the problem size must be positive, found {n}"
            )
        if len(entries) != 2 * n * n:
            raise ValueError(
                f"Invalid instance: expected {2 * n * n} matrix entries after n = {n}, found {len(entries)}"
            )
        if any(v < 0 for v in entries):
            raise ValueError("Invalid instance: matrix entries must be non-negative")

        flow = [entries[i * n : (i + 1) * n] for i in range(n)]
        offset = n * n
        distance = [entries[offset + i * n : offset + (i + 1) * n] for i in range(n)]
        return cls(flow, distance, name)


if __name__ == "__main__":
    import roar_net_api.algorithms as alg

    logging.basicConfig(
        stream=sys.stderr,
        level="INFO",
        format="%(levelname)s;%(asctime)s;%(message)s",
    )

    problem = Problem.from_textio(sys.stdin)

    # There is no constructive interface yet, so the search starts at random.
    solution = problem.random_solution()
    log.info(f"Objective value of the initial solution: {solution.objective_value()}")

    solution = alg.sa(problem, solution, 10.0, 100.0)
    # solution = alg.rls(problem, solution, 10.0)
    # solution = alg.first_improvement(problem, solution)
    # solution = alg.best_improvement(problem, solution)
    log.info(f"Objective value after local search: {solution.objective_value()}")

    solution.to_textio(sys.stdout)
