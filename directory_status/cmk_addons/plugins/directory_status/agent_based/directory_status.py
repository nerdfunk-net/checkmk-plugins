#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026
# SPDX-License-Identifier: GPL-2.0-or-later

"""Checkmk agent-based plug-in (API v2) for directory file count and freshness."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
    StringTable,
    check_levels,
    render,
)


class DirectoryStatus(TypedDict):
    status: str
    count: int | None
    age_newest: float | None
    newest_file: str | None


Section = Mapping[str, DirectoryStatus]


def parse_directory_status(string_table: StringTable) -> Section:
    parsed: dict[str, DirectoryStatus] = {}
    for line in string_table:
        if len(line) < 2:
            continue

        path = line[0]
        status = line[1]
        count: int | None = None
        age_newest: float | None = None
        newest_file: str | None = None

        if len(line) >= 3 and line[2] != "":
            try:
                count = int(line[2])
            except ValueError:
                count = None

        if len(line) >= 4 and line[3] != "":
            try:
                age_newest = float(line[3])
            except ValueError:
                age_newest = None

        if len(line) >= 5 and line[4] != "":
            newest_file = line[4]

        parsed[path] = {
            "status": status,
            "count": count,
            "age_newest": age_newest,
            "newest_file": newest_file,
        }
    return parsed


def discover_directory_status(section: Section) -> DiscoveryResult:
    for path in section:
        yield Service(item=path)


def check_directory_status(
    item: str,
    params: Mapping[str, object],
    section: Section,
) -> CheckResult:
    data = section.get(item)
    if data is None:
        yield Result(state=State.UNKNOWN, summary="Directory not found in agent output")
        return

    if data["status"] != "ok":
        yield Result(state=State.CRIT, summary="Directory does not exist or is not accessible")
        return

    count = data["count"]
    if count is None:
        yield Result(state=State.UNKNOWN, summary="File count missing in agent output")
        return

    yield from check_levels(
        count,
        levels_upper=params.get("maxcount"),  # type: ignore[arg-type]
        metric_name="directory_file_count",
        label="Files",
        render_func=str,
    )

    age_newest = data["age_newest"]
    newest_file = data["newest_file"]

    if count == 0:
        yield Result(state=State.OK, summary="No files in directory")
        return

    if age_newest is None:
        yield Result(state=State.UNKNOWN, summary="Age data missing in agent output")
        return

    if newest_file:
        yield Result(state=State.OK, notice=f"Newest file: {newest_file}")

    yield from check_levels(
        age_newest,
        levels_upper=params.get("maxage_newest"),  # type: ignore[arg-type]
        metric_name="directory_age_newest",
        label="Age of newest file",
        render_func=render.timespan,
    )


agent_section_directory_status = AgentSection(
    name="directory_status",
    parse_function=parse_directory_status,
)

check_plugin_directory_status = CheckPlugin(
    name="directory_status",
    service_name="Directory %s",
    discovery_function=discover_directory_status,
    check_function=check_directory_status,
    check_ruleset_name="directory_status",
    check_default_parameters={
        "maxcount": ("no_levels", None),
        "maxage_newest": ("no_levels", None),
    },
)
