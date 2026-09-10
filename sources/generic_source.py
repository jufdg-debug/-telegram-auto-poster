"""
Adaptador genérico / placeholder.

Use este arquivo como modelo para criar adaptadores de fontes
autorizadas no futuro.

NÃO implementa scraping de sites protegidos.
NÃO tenta contornar autenticação, DRM, CAPTCHA ou paywall.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sources.base import BaseSource, VideoItem

logger = logging.getLogger(__name__)


class GenericSource(BaseSource):
    """
    Stub para fontes futuras.

    Como usar:
    1. Crie um novo arquivo em sources/ (ex: minha_fonte.py)
    2. Herde de BaseSource
    3. Implemente fetch_new_items() de forma legítima
    4. Registre a classe em sources/__init__.py (SOURCE_REGISTRY)
    5. Adicione a configuração em config.py (SOURCES)

    Exemplo mínimo de implementação legítima:

        def fetch_new_items(self) -> List[VideoItem]:
            # 1. Fazer requisição HTTP apenas se a fonte permitir
            # 2. Parsear resposta (JSON, RSS, HTML público sem proteção)
            # 3. Montar VideoItem com content_id único e media_url direto
            # 4. Retornar lista
            return []
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.base_url = config.get("base_url", "")

    def fetch_new_items(self) -> List[VideoItem]:
        logger.warning(
            "[%s] GenericSource é apenas um placeholder. "
            "Nenhum conteúdo será retornado. "
            "Implemente um adaptador específico para sua fonte autorizada.",
            self.name,
        )
        if self.base_url:
            logger.info("[%s] base_url configurada: %s (não usada neste stub)", self.name, self.base_url)
        return []
