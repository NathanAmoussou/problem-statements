<!--
SPDX-FileCopyrightText: 2026 Nathan Amoussou <nathan.amoussou@etu.univ-cotedazur.fr>
SPDX-FileCopyrightText: 2026 Denis Pallez <denis.pallez@univ-cotedazur.fr>

SPDX-License-Identifier: CC-BY-4.0
-->

# Quadratic Assignment Problem

Nathan Amoussou, Université Côte d'Azur, CNRS, I3S, France  
Denis Pallez, Université Côte d'Azur, CNRS, I3S, France

Copyright 2026 Nathan Amoussou and Denis Pallez.

This document is licensed under CC-BY-4.0.

## Introduction

The Quadratic Assignment Problem (QAP) is a classic combinatorial optimisation problem in which $n$ facilities must be assigned to $n$ locations, with exactly one facility per location. A flow is defined between each pair of facilities, and a distance between each pair of locations.

The problem was introduced by Koopmans and Beckmann in 1957 [1], who notably studied the placement of industrial plants with inter-plant transportation costs. Since then, it has been used to formulate a wide range of practical problems, particularly in facility layout and logistics, such as arranging hospital departments to reduce the distance travelled by patients [2]. Despite its simple formulation, the QAP was shown to be NP-hard by Sahni and Gonzalez [3] and is regarded as one of the most difficult combinatorial optimisation problems [4], which has made it the subject of extensive research.

## Task

Determine an assignment of the $n$ facilities to the $n$ locations that minimises the sum, over all ordered pairs of indices $(i,j)$, of the product of the flow from facility $i$ to facility $j$ and the distance between their assigned locations.

## Detailed description

An instance of the QAP is defined by a positive integer $n$, representing the number of facilities and locations, together with two non-negative integer $n \times n$ matrices: a flow matrix $F=(f_{ij})$, where $f_{ij}$ denotes the flow from facility $i$ to facility $j$, and a distance matrix $D=(d_{kl})$, where $d_{kl}$ denotes the distance from location $k$ to location $l$. Neither matrix is assumed to be symmetric. A solution is represented by a permutation $\pi=(\pi(1),\ldots,\pi(n)) \in S_n$, where $S_n$ denotes the set of all permutations of $\lbrace1,\ldots,n\rbrace$ and $\pi(i)$ denotes the location assigned to facility $i$. Since $\pi$ is a permutation, each facility is assigned to exactly one location and each location receives exactly one facility. Every permutation therefore represents a feasible solution, and the problem has no further constraints.

The problem can be stated as

$$
\min_{\pi \in S_n}
\sum_{i=1}^{n}\sum_{j=1}^{n}
f_{ij}d_{\pi(i)\pi(j)}.
$$

Note that the general Koopmans-Beckmann formulation [1] also includes a linear term $\sum_{i=1}^{n} b_{i\pi(i)}$, accounting for the cost of placing facility $i$ at location $\pi(i)$. As is standard in the literature [4], we consider here the quadratic form obtained by omitting this linear term.

## Instance data file

The instance file begins with a positive integer $n$, denoting the number of facilities and locations. It is followed by the $n^2$ integer entries of the flow matrix $F$ in row-major order, and then the $n^2$ integer entries of the distance matrix $D$, also in row-major order. Values are separated by whitespace, and the placement of line breaks is not significant.

Instances are usually laid out with one line per matrix row:

```text
n

f11 f12 ... f1n
f21 f22 ... f2n
... ... ... ...
fn1 fn2 ... fnn

d11 d12 ... d1n
d21 d22 ... d2n
... ... ... ...
dn1 dn2 ... dnn
```

An instance file is invalid if it does not contain exactly $2n^2$ matrix entries after $n$.

## Solution file

The solution file begins with the problem size $n$ and the objective value of the solution. It is followed by $n$ integer values forming a permutation of $\lbrace1,\ldots,n\rbrace$, where the $i$-th value is $\pi(i)$, the location assigned to facility $i$. Values are separated by whitespace, and the placement of line breaks is not significant.

Solutions are usually laid out as follows:

```text
n objective_value
pi(1) pi(2) ... pi(n)
```

A solution file is invalid if the declared problem size does not match the size of the instance, if the $n$ values do not form a permutation of $\lbrace1,\ldots,n\rbrace$, or if the declared objective value does not equal the value recomputed from the instance and the permutation.

## Example

### Instance

The following instance file describes a QAP instance with three facilities and three locations, with the flow matrix $F$ followed by the distance matrix $D$, neither of which is symmetric:

```text
3

0 3 1
2 0 1
3 1 0

0 1 3
3 0 1
3 2 0
```

### Solution

A feasible solution, which happens to be optimal for this instance, is:

```text
3 19
2 3 1
```

This corresponds to the permutation $\pi=(2,3,1)$, with objective value $19$.

### Explanation

The permutation assigns facility $1$ to location $2$, facility $2$ to location $3$, and facility $3$ to location $1$. Its objective value is

$$
\begin{aligned}
& f_{12}d_{23} + f_{13}d_{21} + f_{21}d_{32} + f_{23}d_{31} + f_{31}d_{12} + f_{32}d_{13} \\
&= 3\cdot 1 + 1\cdot 3 + 2\cdot 2 + 1\cdot 3 + 3\cdot 1 + 1\cdot 3 \\
&= 19.
\end{aligned}
$$

In this instance, the diagonal terms are zero and therefore do not contribute to the objective value.

## Problem instances

A large collection of QAP instances, together with best-known or optimal solutions for many of them, is available from [QAPLIB](https://doi.org/10.7488/ds/3428) [5]. Instance files use the `.dat` extension and the layout described above, although QAPLIB denotes the two matrices generically as $A$ and $B$ and does not prescribe a universal flow-distance order. Solution files use the `.sln` extension and also generally follow the format described above, but some legacy files use different separators or indexing conventions and may require normalisation.

## Acknowledgements

This problem statement is based upon work from COST Action Randomised
Optimisation Algorithms Research Network (ROAR-NET), CA22137, is supported by
COST (European Cooperation in Science and Technology).

## References

[1] T. C. Koopmans and M. J. Beckmann. "Assignment Problems and the Location of Economic Activities." Econometrica, 25(1):53-76, 1957. [10.2307/1907742](https://doi.org/10.2307/1907742)

[2] A. N. Elshafei. "Hospital Layout as a Quadratic Assignment Problem." Operational Research Quarterly, 28(1):167-179, 1977. [10.1057/jors.1977.29](https://doi.org/10.1057/jors.1977.29)

[3] S. Sahni and T. Gonzalez. "P-Complete Approximation Problems." Journal of the ACM, 23(3):555-565, 1976. [10.1145/321958.321975](https://doi.org/10.1145/321958.321975)

[4] E. M. Loiola, N. M. M. de Abreu, et al. "A Survey for the Quadratic Assignment Problem." European Journal of Operational Research, 176(2):657-690, 2007. [10.1016/j.ejor.2005.09.032](https://doi.org/10.1016/j.ejor.2005.09.032)

[5] R. E. Burkard, S. E. Karisch, et al. "QAPLIB - A Quadratic Assignment Problem Library." Journal of Global Optimization, 10:391–403, 1997. [10.1023/A:1008293323270](https://doi.org/10.1023/A:1008293323270)
