#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026
# SPDX-License-Identifier: GPL-2.0-or-later

"""WATO rulesets for directory_status (check parameters + agent configuration)."""

from __future__ import annotations

from cmk.rulesets.v1 import Help, Label, Message, Title
from cmk.rulesets.v1.form_specs import (
    CascadingSingleChoice,
    CascadingSingleChoiceElement,
    DefaultValue,
    DictElement,
    Dictionary,
    FieldSize,
    FixedValue,
    InputHint,
    Integer,
    LevelDirection,
    LevelsType,
    List,
    SimpleLevels,
    String,
    TimeMagnitude,
    TimeSpan,
    validators,
)
from cmk.rulesets.v1.form_specs.validators import ValidationError
from cmk.rulesets.v1.rule_specs import (
    AgentConfig,
    CheckParameters,
    HostAndItemCondition,
    Topic,
)

_DISPLAYED_MAGNITUDES_TIME = [
    TimeMagnitude.DAY,
    TimeMagnitude.HOUR,
    TimeMagnitude.MINUTE,
    TimeMagnitude.SECOND,
]


def _validate_absolute_directory_path(value: str) -> None:
    if not value.startswith("/"):
        raise ValidationError(Message("Directory path must be absolute (start with /)."))
    if "|" in value:
        raise ValidationError(Message("Directory path must not contain the '|' character."))


def _parameter_form_directory_status() -> Dictionary:
    return Dictionary(
        elements={
            "maxcount": DictElement(
                required=False,
                parameter_form=SimpleLevels(
                    title=Title("Maximum number of files"),
                    help_text=Help(
                        "Upper levels for the number of regular files in the directory. "
                        "Subdirectories are not counted."
                    ),
                    level_direction=LevelDirection.UPPER,
                    prefill_levels_type=DefaultValue(LevelsType.FIXED),
                    prefill_fixed_levels=InputHint((100, 200)),
                    form_spec_template=Integer(unit_symbol="files"),
                ),
            ),
            "maxage_newest": DictElement(
                required=False,
                parameter_form=SimpleLevels(
                    title=Title("Maximum age of newest file"),
                    help_text=Help(
                        "Upper levels for the time that may have elapsed since the newest "
                        "regular file in the directory was last modified. An empty "
                        "directory never triggers this threshold."
                    ),
                    level_direction=LevelDirection.UPPER,
                    prefill_levels_type=DefaultValue(LevelsType.FIXED),
                    prefill_fixed_levels=InputHint((3600.0, 7200.0)),
                    form_spec_template=TimeSpan(
                        displayed_magnitudes=_DISPLAYED_MAGNITUDES_TIME,
                    ),
                ),
            ),
        }
    )


rule_spec_directory_status = CheckParameters(
    name="directory_status",
    title=Title("Directory status (file count and freshness)"),
    topic=Topic.STORAGE,
    parameter_form=_parameter_form_directory_status,
    condition=HostAndItemCondition(item_title=Title("Directory path")),
)


def _parameter_form_directory_status_bakery() -> Dictionary:
    return Dictionary(
        help_text=Help(
            "Deploy the <tt>directory_status</tt> agent plug-in and configure which "
            "directories should be monitored on the target host."
        ),
        elements={
            "deployment": DictElement(
                required=True,
                parameter_form=CascadingSingleChoice(
                    title=Title("Deployment type"),
                    prefill=DefaultValue("sync"),
                    elements=(
                        CascadingSingleChoiceElement(
                            name="sync",
                            title=Title("Deploy the plug-in and run it synchronously"),
                            parameter_form=FixedValue(value=None),
                        ),
                        CascadingSingleChoiceElement(
                            name="cached",
                            title=Title("Deploy the plug-in and run it asynchronously"),
                            parameter_form=TimeSpan(
                                displayed_magnitudes=(
                                    TimeMagnitude.HOUR,
                                    TimeMagnitude.MINUTE,
                                ),
                                custom_validate=(
                                    validators.NumberInRange(min_value=60.0),
                                ),
                            ),
                        ),
                        CascadingSingleChoiceElement(
                            name="do_not_deploy",
                            title=Title("Do not deploy the plug-in"),
                            parameter_form=FixedValue(value=None),
                        ),
                    ),
                ),
            ),
            "directories": DictElement(
                required=True,
                parameter_form=List(
                    title=Title("Directories to monitor"),
                    help_text=Help(
                        "Absolute paths of directories on the monitored host. Only regular "
                        "files directly in each directory are counted (not recursive). "
                        "Symbolic links to files are not counted."
                    ),
                    element_template=String(
                        title=Title("Directory path"),
                        field_size=FieldSize.LARGE,
                        custom_validate=(
                            validators.LengthInRange(min_value=1),
                            _validate_absolute_directory_path,
                        ),
                    ),
                    custom_validate=(validators.LengthInRange(min_value=1),),
                    add_element_label=Label("Add directory"),
                ),
            ),
        },
    )


rule_spec_directory_status_bakery = AgentConfig(
    name="directory_status",
    title=Title("Directory status (Linux)"),
    topic=Topic.STORAGE,
    parameter_form=_parameter_form_directory_status_bakery,
)
