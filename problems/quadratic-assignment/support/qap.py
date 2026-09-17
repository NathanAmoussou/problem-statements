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
    def __init__(
        self,
        problem: Problem,
        permutation: list[int],
        objective: int,
        deltas: list[list[int]] | None,
    ):
        self.problem = problem
        # permutation[i] is the location assigned to facility i, from 0
        self.permutation = permutation
        self.objective = objective
        # Taillard delta matrix
        # e.g.:
        # [[],
        # [Δ01],
        # [Δ02, Δ12],
        # [Δ03, Δ13, Δ23]]
        self.deltas = deltas

    def __str__(self) -> str:
        return " ".join(str(location + 1) for location in self.permutation)

    def to_textio(self, f: TextIO) -> None:
        """
        Write the solution to a text I/O destination `f` in the format of the
        problem statement, where locations are numbered from 1.
        """
        f.write(f"{self.problem.n} {self.objective}\n{self}\n")

    def copy_solution(self) -> Self:
        # For GA potentially lot of copies, will have to look for techniques to speed up
        deltas = None if self.deltas is None else [row.copy() for row in self.deltas]
        return self.__class__(
            self.problem, self.permutation.copy(), self.objective, deltas
        )

    def objective_value(self) -> int:
        """
        Return the objective value of the solution, which is held rather than
        computed. Every permutation is feasible, so it is never undefined.
        """
        # python -O to drop the assertion
        assert self.objective == self.problem._evaluate(self.permutation)
        return self.objective


# ----------------------------------- Move -----------------------------------


@final
class SwapMove(
    SupportsApplyMove[Solution],
    SupportsObjectiveValueIncrement[Solution],
):
    def __init__(self, neighbourhood: SwapNeighbourhood, r: int, s: int):
        self.neighbourhood = neighbourhood
        self.r = r
        self.s = s

    def __str__(self) -> str:
        return f"Move: exchange the locations of facilities {self.r} and {self.s}"

    @staticmethod
    def _burkard_delta(
        problem: Problem, permutation: Sequence[int], r: int, s: int
    ) -> int:
        """
        Return the objective value delta caused by swapping locations of
        facilities r and s in the permutation, using Burkard and Rendl 1984
        O(n) formula. Valid for any matrices, symmetric or not, with any
        diagonals. DOI: 10.1016/0377-2217(84)90231-5
        """
        f, d, n = problem.flow, problem.distance, problem.n
        pi = permutation
        a, b = pi[r], pi[s]

        increment = 0
        for k in range(n):
            if k == r or k == s:
                continue
            c = pi[k]
            increment += f[r][k] * (d[b][c] - d[a][c]) + f[k][r] * (d[c][b] - d[c][a])
            increment += f[s][k] * (d[a][c] - d[b][c]) + f[k][s] * (d[c][a] - d[c][b])

        increment += f[r][r] * (d[b][b] - d[a][a]) + f[s][s] * (d[a][a] - d[b][b])
        increment += f[r][s] * (d[b][a] - d[a][b]) + f[s][r] * (d[a][b] - d[b][a])
        return increment

    @staticmethod
    def _taillard_delta(
        problem: Problem,
        permutation: Sequence[int],
        delta: int,
        u: int,
        v: int,
        r: int,
        s: int,
    ) -> int:
        """
        Return the delta of exchanging locations of facilities u and v after
        those of r and s have just been exchanged, given the delta it
        had before, using Taillard 1995 O(1) formula. The {u, v} and {r, s}
        pairs must be disjoint, else Burkard and Rendl 1984 O(n) formula is
        used. DOI: 10.1016/0966-8349(95)00008-6

        """
        f, d = problem.flow, problem.distance
        pi = permutation
        pr, ps, pu, pv = pi[r], pi[s], pi[u], pi[v]
        return (
            delta
            + (f[r][u] - f[r][v] + f[s][v] - f[s][u])
            * (d[ps][pu] - d[ps][pv] + d[pr][pv] - d[pr][pu])
            + (f[u][r] - f[v][r] + f[v][s] - f[u][s])
            * (d[pu][ps] - d[pv][ps] + d[pv][pr] - d[pu][pr])
        )

    def _update_deltas(self, solution: Solution, delta: int) -> None:
        """
        Updates Taillard 1995's approach delta matrix after the move has been
        applied, `delta` being the value the move had before. Called by
        `apply_move` once the locations have been exchanged, so every
        formula below reads the new permutation. Three cases, O(n^2) in all:
          - the O(n^2) pairs disjoint from {r, s}, almost all of them:
            `_taillard_delta` from their previous value, O(1) each
          - the 2(n-2) in O(n) pairs sharing one facility with (r, s):
            `_burkard_delta` from the instance data, O(n) each
          - (r, s) itself: exchanging back undoes the move, so its delta is
            the opposite of what it was, and it is skipped by the loop.
        """
        problem, pi, deltas = solution.problem, solution.permutation, solution.deltas
        assert deltas is not None
        r, s = self.r, self.s
        for v in range(problem.n):
            row = deltas[v]
            for u in range(v):
                if u == r or u == s or v == r or v == s:
                    if u == r and v == s:
                        continue
                    row[u] = self._burkard_delta(problem, pi, u, v)
                else:
                    row[u] = self._taillard_delta(problem, pi, row[u], u, v, r, s)
        deltas[s][r] = -delta

    def objective_value_increment(self, solution: Solution) -> int:
        """
        Return the delta of the objective value that applying the move would
        cause, without modifying the solution. A O(1) lookup when the solution
        carries its delta table and the O(n) formula otherwise.
        """
        if solution.deltas is None:
            return self._burkard_delta(
                solution.problem, solution.permutation, self.r, self.s
            )
        return solution.deltas[self.s][self.r]

    def apply_move(self, solution: Solution) -> Solution:
        """
        Exchange the locations of the two facilities in place, and update the
        objective value held by the solution, and its delta table if it has
        one.
        """
        delta = self.objective_value_increment(solution)
        solution.objective += delta
        pi, r, s = solution.permutation, self.r, self.s
        pi[r], pi[s] = pi[s], pi[r]
        if solution.deltas is not None:
            self._update_deltas(solution, delta)
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
        fast_evaluation: bool = True,
    ):
        self.flow = tuple(tuple(row) for row in flow)
        self.distance = tuple(tuple(row) for row in distance)
        self.name = name
        self.n = len(self.flow)
        # Whether solutions carry a table of the deltas of every exchange,
        # maintained after each move so that an increment is a lookup rather
        # than an O(n) computation. Off, deltas are computed on request.
        self.fast_evaluation = fast_evaluation
        self.l_nbhood: SwapNeighbourhood | None = None

    def __str__(self) -> str:
        rows = lambda matrix: "\n".join(" ".join(map(str, row)) for row in matrix)
        return f"{self.n}\n\n{rows(self.flow)}\n\n{rows(self.distance)}"

    def _evaluate(self, permutation: Sequence[int]) -> int:
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

    def _delta_matrix(self, permutation: Sequence[int]) -> list[list[int]]:
        """
        Return the objective value deltas of every swap, computed from
        scratch, as a triangular table whose entry [s][r], for r < s, is the
        increment of exchanging the locations of facilities r and s.

        This is O(n^3), n(n-1)/2 deltas of O(n) each, and is only done
        when a solution is createds.
        """
        return [
            [SwapMove._burkard_delta(self, permutation, r, s) for r in range(s)]
            for s in range(self.n)
        ]

    def local_neighbourhood(self) -> SwapNeighbourhood:
        """
        Return the neighbourhood in which two solutions are neighbours when
        one is obtained from the other by swapping the locations of two
        facilities.
        """
        if self.l_nbhood is None:
            self.l_nbhood = SwapNeighbourhood(self)
        return self.l_nbhood

    def random_solution(self) -> Solution:
        """
        Return a solution drawn uniformly at random, to be used as a starting
        point. Every permutation is feasible, so shuffling is enough.

        This is the only place where the objective value, and the increment
        table when fast_evaluation is set, are computed from scratch, since the
        solution it returns has no predecessor to derive them from.
        """
        permutation = random.sample(range(self.n), self.n)
        # permutation = list(range(self.n))
        # random.shuffle(permutation)
        deltas = self._delta_matrix(permutation) if self.fast_evaluation else None
        return Solution(self, permutation, self._evaluate(permutation), deltas)

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
