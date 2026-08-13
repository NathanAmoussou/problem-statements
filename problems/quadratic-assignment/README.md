<!--
SPDX-FileCopyrightText: 2026 Nathan Amoussou <nathan.amoussou@etu.univ-cotedazur.fr>

SPDX-License-Identifier: CC-BY-4.0
-->

<!-- Replace the comment above with your licence information for your problem
statement. Consider all copyright holders and contributors. -->

<!-- According to the copyright and licensing policy of ROAR-NET original
problem statements contributed to this repository shall be licensed under the
CC-BY-4.0 licence. In some cases CC-BY-SA-4.0 might be accepted, e.g., if the
problem is based upon an existing problem licensed under those terms. Please
provide a clear justification when opening the pull request if the problem is
not licensed under CC-BY-4.0 -->

<!-- Remove the section below before submitting -->

# Problem template


This folder provides a template for problem statements.

Replace the problem statement below according to the instructions within that
file (and remove this section).

Place any images and figures in the `images` folder.

Place instance data in the `data` folder. The organisation within that folder is
merely a suggestion and may be adapted according to the problem needs.

Place any support material (e.g., instance generators, solution evaluators,
solution visualisers) in the `support` folder.

Template follows below.

---

<!-- Remove the section above before submitting -->

# Quadratic Assignment Problem

Nathan Amoussou, Université Côte d'Azur, CNRS, I3S, France

<!-- Put two empty spaces at the end of each author line except the last for
proper formatting -->

Copyright 2026 Nathan Amoussou.

This document is licensed under CC-BY-4.0.

<!-- Complete the above accordingly. Copyright and licensing information must be
consistent with the comment at the beggining of the markdown file -->

## Introduction

The Quadratic Assignment Problem (QAP) is a classic combinatorial optimisation problem in which $n$ facilities must be assigned to $n$ locations, with exactly one facility per location. A flow is defined between each pair of facilities, and a distance between each pair of locations. The objective is to find an assignment that minimises the overall quadratic cost obtained by combining these flows and distances.

The problem was introduced by Koopmans and Beckmann in 1957 [1], who notably studied the placement of industrial plants with inter-plant transportation costs. Since then, it has been used to formulate a wide range of practical problems, particularly in facility layout and logistics, such as arranging hospital departments to reduce transportation and communication costs [2]. Despite its simple formulation, the QAP was shown to be NP-hard by Sahni and Gonzalez [3] and is regarded as one of the most difficult combinatorial optimisation problems [4], which has made it the subject of extensive research.

## Task

Describe the high-level optimisation task in one or two sentences.

## Detailed description

Provide a detailed description of the problem in this section. This should
detail what parameters characterise a problem instance, what characterises a
solution, how a solution is evaluated (e.g. an objective function), and solution
feasibility constraints.

## Instance data file

Describe the format of a problem instance file.

## Solution file

Describe the format of a solution file.

## Example

### Instance

Provide a small example instance in the described format.

### Solution

Provide a feasible solution to the example instance in the described format
(including its evaluation measure).

### Explanation

Optionally, provide a descriptive and/or visual explanation of the solution (and
its evaluation measure value) for the instance.

## Acknowledgements

This problem statement is based upon work from COST Action Randomised
Optimisation Algorithms Research Network (ROAR-NET), CA22137, is supported by
COST (European Cooperation in Science and Technology).

<!-- Please keep the above acknowledgement. Add any other acknowledgements as
relevant. -->

## References

[1] T. C. Koopmans and M. J. Beckmann. "Assignment Problems and the Location of Economic Activities." Econometrica, 25(1):53–76, 1957. [10.2307/1907742](https://doi.org/10.2307/1907742)

[2] A. N. Elshafei. "Hospital Layout as a Quadratic Assignment Problem." Operational Research Quarterly, 28(1):167–179, 1977. [10.1057/jors.1977.29](https://doi.org/10.1057/jors.1977.29)

[3] S. Sahni and T. Gonzalez. "P-Complete Approximation Problems." Journal of the ACM, 23(3):555–565, 1976. [10.1145/321958.321975](https://doi.org/10.1145/321958.321975)

[4] E. M. Loiola, N. M. M. de Abreu, et al. "A Survey for the Quadratic Assignment Problem." European Journal of Operational Research, 176(2):657–690, 2007. [10.1016/j.ejor.2005.09.032](https://doi.org/10.1016/j.ejor.2005.09.032)
