"""The runners for different languages."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from leet import runner

from .python3 import Python3Runner

LANG_TO_RUNNER: dict[str, type[runner.Runner]] = {
    "python3": Python3Runner,
}
