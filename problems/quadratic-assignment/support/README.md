<!--
SPDX-FileCopyrightText: 2026 Nathan Amoussou <nathan.amoussou@etu.univ-cotedazur.fr>

SPDX-License-Identifier: CC-BY-4.0
-->

# Quadratic Assignment Problem: Support Resources

This directory contains some support code for the Quadratic Assignment
problem. In particular:

- `generator.py` is a utility to generate new instances. It requires `python3`.
- `evaluation.py` is a utility to validate a solution against an instance and recompute its objective value. It requires `python3`.
- `qap.py` is a model for the [roar-net-api-py](https://github.com/roar-net/roar-net-api-py) python library to solve the problem. It requires `python3` and the `roar-net-api` package.

Both utilities describe their usage and their options in their module docstring, and `--help` lists the options of `generator.py`.
