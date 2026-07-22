#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026
# SPDX-License-Identifier: GPL-2.0-or-later

"""Metric definitions for directory_status."""

from __future__ import annotations

from cmk.graphing.v1 import Title
from cmk.graphing.v1.metrics import (
    Color,
    DecimalNotation,
    Metric,
    StrictPrecision,
    TimeNotation,
    Unit,
)
from cmk.graphing.v1.perfometers import Closed, FocusRange, Open, Perfometer

metric_directory_file_count = Metric(
    name="directory_file_count",
    title=Title("Directory file count"),
    unit=Unit(DecimalNotation(""), StrictPrecision(0)),
    color=Color.BLUE,
)

metric_directory_age_newest = Metric(
    name="directory_age_newest",
    title=Title("Age of newest file in directory"),
    unit=Unit(TimeNotation()),
    color=Color.ORANGE,
)

perfometer_directory_status_file_count = Perfometer(
    name="directory_status_file_count",
    focus_range=FocusRange(Closed(0), Open(100)),
    segments=["directory_file_count"],
)
