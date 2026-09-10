"""
Fábrica de fontes.
Adicione novos adaptadores aqui quando criar fontes autorizadas.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sources.base import BaseSource, VideoItem
from sources.example_source import ExampleSource
from sources.generic_source import GenericSource

logger = logging.getLogger(__name__)

# Mapa de type -> classe
SOURCE_REGISTRY = {
    "example": ExampleSource,
    "generic": GenericSource,
}


def create_source(config: Dict[str, Any]) -> BaseSource:
    """Cria uma instância de fonte a partir do dicionário de configuração."""
    source_type = config.get("type", "").lower().strip()
    if source_type not in SOURCE_REGISTRY:
        raise ValueError(
            f"Tipo de fonte desconhecido: '{source_type}'. "
            f"Disponíveis: {list(SOURCE_REGISTRY.keys())}"
        )
    cls = SOURCE_REGISTRY[source_type]
    return cls(config)


def get_all_sources(source_configs: List[Dict[str, Any]]) -> List[BaseSource]:
    sources = []
    for cfg in source_configs:
        try:
            src = create_source(cfg)
            sources.append(src)
            logger.info("Fonte carregada: %s (%s)", src.name, cfg.get("type"))
        except Exception as e:
            logger.error("Não foi possível carregar fonte %s: %s", cfg, e)
    return sources


__all__ = [
    "BaseSource",
    "VideoItem",
    "create_source",
    "get_all_sources",
    "ExampleSource",
    "GenericSource",
]
