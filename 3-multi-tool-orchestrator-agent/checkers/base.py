"""Checker contract — one common interface, several independent implementations."""

from abc import ABC, abstractmethod

from domain.models import Finding, PipelineDefinition


class Checker(ABC):
    """Every checker inspects the parsed pipeline and returns whatever it finds. Never raises."""

    @abstractmethod
    def check(self, pipeline: PipelineDefinition) -> list[Finding]:
        pass
