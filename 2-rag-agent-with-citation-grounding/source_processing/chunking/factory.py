"""Create chunking strategies from their configured names."""

from collections.abc import Callable

from source_processing.chunking.interfaces import ChunkingStrategy
from source_processing.chunking.section_strategy import SectionAsChunkStrategy
from source_processing.chunking.structural_strategy import StructuralBlocksStrategy


class ChunkingStrategyFactory:
    """Create strategies from builders registered by the application."""

    def __init__(self) -> None:
        self._strategy_builders: dict[str, Callable[[], ChunkingStrategy]] = {}

    def register(
        self,
        strategy_name: str,
        strategy_builder: Callable[[], ChunkingStrategy],
    ) -> None:
        """Register one strategy builder under a normalized name."""

        name = strategy_name.strip().lower()
        if not name:
            raise ValueError("strategy_name must be non-empty text")
        if name in self._strategy_builders:
            raise ValueError(f"Strategy is already registered: {strategy_name}")
        self._strategy_builders[name] = strategy_builder

    def create(self, strategy_name: str) -> ChunkingStrategy:
        """Create a new strategy instance requested by name."""

        name = strategy_name.strip().lower()
        strategy_builder = self._strategy_builders.get(name)
        if strategy_builder is None:
            raise ValueError(f"Unsupported chunking strategy: {strategy_name}")
        return strategy_builder()


def build_default_chunking_strategy_factory() -> ChunkingStrategyFactory:
    """Return a factory with all strategies currently shipped by this project."""

    factory = ChunkingStrategyFactory()
    factory.register(SectionAsChunkStrategy.name, SectionAsChunkStrategy)
    factory.register(StructuralBlocksStrategy.name, StructuralBlocksStrategy)
    return factory
