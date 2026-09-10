"""
Classe base e modelo de dados para todas as fontes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VideoItem:
    """Representa um conteúdo de vídeo detectado por uma fonte."""

    # Identificador único (URL, ID da postagem, hash, etc.)
    content_id: str

    # URL da página ou do item (para referência)
    page_url: str

    # Título / descrição curta
    title: str = ""

    # URL direta do arquivo de vídeo (quando a fonte permite download legítimo)
    # Se None, o sistema não tentará baixar.
    media_url: Optional[str] = None

    # Metadados extras opcionais
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.content_id:
            raise ValueError("content_id é obrigatório")


class BaseSource(ABC):
    """
    Interface que toda fonte deve implementar.

    Regras importantes:
    - Só retorne itens que você tem autorização para baixar e redistribuir.
    - Nunca tente contornar login, paywall, DRM, CAPTCHA ou bloqueios.
    - Se a fonte não permitir acesso automatizado legítimo, levante uma
      exceção clara ou retorne lista vazia com log de erro.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.name: str = config.get("name", self.__class__.__name__)
        self.max_items: int = int(config.get("max_items", 5))

    @abstractmethod
    def fetch_new_items(self) -> List[VideoItem]:
        """
        Retorna lista de itens novos (ou candidatos) detectados nesta execução.
        A filtragem de "já publicado" é feita pelo main.py usando o database.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
