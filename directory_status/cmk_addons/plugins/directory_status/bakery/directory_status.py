#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026
# SPDX-License-Identifier: GPL-2.0-or-later

"""Agent bakery plug-in for directory_status."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from cmk.bakery.v2_unstable import BakeryPlugin, OS, Plugin, PluginConfig


class _Config(BaseModel):
    deployment: tuple[Literal["do_not_deploy", "sync", "cached"], float | None]
    directories: list[str] = []


def _config_lines(directories: list[str]) -> list[str]:
    return ["# One directory path per line", *directories]


def get_directory_status_files(conf: _Config) -> Iterable[Plugin | PluginConfig]:
    if conf.deployment[0] == "do_not_deploy":
        return

    yield Plugin(
        base_os=OS.LINUX,
        source=Path("directory_status"),
        interval=conf.deployment[1],
    )

    if conf.directories:
        yield PluginConfig(
            base_os=OS.LINUX,
            lines=_config_lines(conf.directories),
            target=Path("directory_status.cfg"),
            include_header=True,
        )


bakery_plugin_directory_status = BakeryPlugin(
    name="directory_status",
    parameter_parser=_Config.model_validate,
    default_parameters=None,
    files_function=get_directory_status_files,
)
