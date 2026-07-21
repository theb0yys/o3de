#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
"""Semantic validation for the deterministic Actor/Troop fixture catalog."""

from __future__ import annotations

from typing import Any

from population_preview_fixture_catalog_history import (
    validate_relationships_and_history,
)
from population_preview_fixture_catalog_records import (
    validate_records_and_actors,
)
from population_preview_fixture_catalog_troops import (
    validate_troops_and_members,
)


def validate_catalog(
    catalog: dict[str, Any],
    evidence_by_id: dict[str, dict[str, Any]],
) -> None:
    records, actor_profiles = validate_records_and_actors(
        catalog,
        evidence_by_id,
    )
    validate_troops_and_members(
        catalog,
        evidence_by_id,
        records,
        actor_profiles,
    )
    validate_relationships_and_history(
        catalog,
        evidence_by_id,
        records,
    )
