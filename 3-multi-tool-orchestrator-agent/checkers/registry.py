"""Collects every built-in checker. Add new ones here only."""

from checkers.base import Checker
from checkers.orphan_job import OrphanJobChecker
from checkers.self_dependency import SelfDependencyChecker
from checkers.undefined_stage import UndefinedStageChecker


def build_default_checkers() -> list[Checker]:
    return [
        UndefinedStageChecker(),
        OrphanJobChecker(),
        SelfDependencyChecker(),
    ]
