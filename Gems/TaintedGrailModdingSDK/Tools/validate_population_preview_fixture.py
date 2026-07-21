#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
"""Run the focused Actor/Troop population fixture validator."""

from validate_population_preview_fixture_core import (
    main,
    validate_population_preview_fixture,
)

__all__ = ["main", "validate_population_preview_fixture"]


if __name__ == "__main__":
    raise SystemExit(main())
