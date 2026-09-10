"""
Fonte de exemplo SEGURA e autorizada para testes.

Usa vídeos de domínio público / CC0 / samples públicos conhecidos.
Não baixa conteúdo de Erome ou qualquer site adulto.
Não contorna nenhuma proteção.

Serve apenas para validar o fluxo completo:
detectar → verificar duplicata → baixar → enviar → registrar.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sources.base import BaseSource, VideoItem

logger = logging.getLogger(__name__)

# Lista fixa de vídeos de teste públicos e legítimos.
# Estes links são samples amplamente usados para desenvolvimento.
SAMPLE_VIDEOS = [
    {
        "content_id": "sample-mdn-flower",
        "title": "Flower (MDN / CC0 sample)",
        "page_url": "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
        "media_url": "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
    },
    {
        "content_id": "sample-bigbuckbunny-10s",
        "title": "Big Buck Bunny – 10s clip (test-videos.co.uk)",
        "page_url": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4",
        "media_url": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4",
    },
    {
        "content_id": "sample-truefilesize-1mb",
        "title": "Sample 1MB MP4 (TrueFileSize / CC0)",
        "page_url": "https://cdn.truefilesize.com/mp4/sample-1mb.mp4",
        "media_url": "https://cdn.truefilesize.com/mp4/sample-1mb.mp4",
    },
]


class ExampleSource(BaseSource):
    """Fonte de demonstração com vídeos públicos de teste."""

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)

    def fetch_new_items(self) -> List[VideoItem]:
        logger.info("[%s] Carregando lista de vídeos de teste públicos...", self.name)

        items: List[VideoItem] = []
        for raw in SAMPLE_VIDEOS[: self.max_items]:
            try:
                item = VideoItem(
                    content_id=raw["content_id"],
                    page_url=raw["page_url"],
                    title=raw["title"],
                    media_url=raw["media_url"],
                    extra={"source_type": "example"},
                )
                items.append(item)
            except Exception as e:
                logger.warning("Item de exemplo inválido ignorado: %s", e)

        logger.info("[%s] %d item(ns) candidato(s) encontrado(s)", self.name, len(items))
        return items
