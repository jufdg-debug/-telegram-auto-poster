"""Vídeos de álbuns autorizados acessíveis por link, sem autenticação."""

from __future__ import annotations

import hashlib
import logging
import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

from config import REQUEST_TIMEOUT
from database import get_published_ids
from sources.base import BaseSource, VideoItem

logger = logging.getLogger(__name__)
USER_AGENT = "Mozilla/5.0 (compatible; telegram-auto-poster/1.0)"
ALBUM_PATH = re.compile(r"^/a/[A-Za-z0-9]+/?$")
PROFILE_PATH = re.compile(r"^/[A-Za-z0-9_-]+/?$")
RESERVED = {"", "login", "logout", "signup", "register", "search", "explore", "new", "top", "upload", "account", "settings"}


def page_url(value: str) -> str:
    """Aceita somente páginas HTTPS do Erome, nunca endereços arbitrários."""
    parsed = urlsplit(value.strip())
    if (parsed.scheme != "https" or parsed.hostname not in {"erome.com", "www.erome.com"}
            or parsed.username or parsed.password or parsed.port not in (None, 443)):
        raise ValueError("Use um link HTTPS de álbum ou perfil do Erome.")
    if not ALBUM_PATH.fullmatch(parsed.path):
        if not PROFILE_PATH.fullmatch(parsed.path) or parsed.path.strip("/").lower() in RESERVED:
            raise ValueError("O link deve apontar para um álbum ou perfil específico.")
    query = parsed.query
    if not ALBUM_PATH.fullmatch(parsed.path):
        params = dict(parse_qsl(query))
        params["t"] = "posts"  # Só os álbuns do próprio perfil, sem repostagens.
        query = urlencode(params)
    return urlunsplit(("https", "www.erome.com", parsed.path.rstrip("/"), query, ""))


def media_url(value: str, album: str) -> str | None:
    parsed = urlsplit(urljoin(album, value))
    host = parsed.hostname or ""
    if (parsed.scheme != "https" or parsed.username or parsed.password
            or parsed.port not in (None, 443)
            or not (host == "erome.com" or host.endswith(".erome.com"))):
        return None
    if not parsed.path.lower().endswith((".mp4", ".webm", ".mov", ".m4v")):
        return None
    return urlunsplit(parsed._replace(fragment=""))


def album_items(html: str, album: str) -> list[VideoItem]:
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.select_one("#album-title, h1")
    title_meta = soup.select_one('meta[property="og:title"]')
    title = (title_node.get_text(" ", strip=True) if title_node else
             (title_meta.get("content", "Vídeo") if title_meta else "Vídeo"))
    items, seen = [], set()
    album_id = urlsplit(album).path.strip("/").split("/")[-1]
    for video in soup.select("video"):
        # Uma única mídia por player, mesmo quando há várias resoluções.
        candidates = [video.get("src"), video.get("data-src")]
        candidates += [node.get("src") or node.get("data-src") for node in video.select("source")]
        direct = next((url for value in candidates if value and (url := media_url(value, album))), None)
        if not direct:
            continue
        group = video.find_parent(class_="media-group")
        stable = group.get("id") if group else None
        # URLs assinadas e mudanças de servidor não geram republicações.
        stable = stable or urlsplit(direct).path
        digest = hashlib.sha256(f"{album_id}:{stable}".encode()).hexdigest()[:32]
        content_id = f"erome:{digest}"
        if content_id in seen:
            continue
        seen.add(content_id)
        items.append(VideoItem(
            content_id=content_id, page_url=album, title=title, media_url=direct,
            extra={"source_type": "erome", "download_headers": {"Referer": album, "User-Agent": USER_AGENT}},
        ))
    return items


class EromeSource(BaseSource):
    def __init__(self, config):
        super().__init__(config)
        raw = config.get("urls", [])
        if isinstance(raw, str):
            raw = re.split(r"[\s,]+", raw.strip())
        self.urls = list(dict.fromkeys(page_url(value) for value in raw if value.strip()))
        self.max_pages = max(1, int(config.get("max_pages", 10)))
        self.max_albums = max(1, int(config.get("max_albums", 100)))
        self.max_items = max(1, self.max_items)
        if not self.urls:
            raise ValueError("Configure EROME_URLS com o link do seu álbum ou perfil.")

    def _read(self, session, url):
        try:
            # Valida cada redirecionamento antes de enviar a requisição seguinte.
            for _ in range(5):
                with session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=False, stream=True) as response:
                    if response.is_redirect:
                        url = page_url(urljoin(url, response.headers.get("Location", "")))
                        continue
                    if response.status_code in (401, 403, 429):
                        raise RuntimeError("Erome recusou o acesso ou limitou as requisições. Tente depois; nenhum bloqueio será contornado.")
                    response.raise_for_status()
                    if "text/html" not in response.headers.get("Content-Type", "").lower():
                        raise RuntimeError("A fonte não retornou uma página HTML.")
                    chunks, total = [], 0
                    for chunk in response.iter_content(65536):
                        total += len(chunk)
                        if total > 5 * 1024 * 1024:
                            raise RuntimeError("Página excedeu o limite de leitura.")
                        chunks.append(chunk)
                    body = b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
                    if "<title>Please wait a few moments</title>" in body:
                        raise RuntimeError("Erome apresentou uma verificação de acesso. Leitura interrompida.")
                    return body, url
            raise RuntimeError("Excesso de redirecionamentos na fonte.")
        except requests.RequestException:
            # Não inclui links privados nos logs.
            raise RuntimeError("Não foi possível ler a página do Erome (rede ou HTTP).") from None

    def fetch_new_items(self):
        published = get_published_ids()
        items, seen, visited, albums = [], set(), set(), set()
        with requests.Session() as session:
            session.headers.update({"User-Agent": USER_AGENT})
            for root in self.urls:
                queue, pages = [root], 0
                while queue and pages < self.max_pages:
                    url = queue.pop(0)
                    if url in visited:
                        continue
                    visited.add(url)
                    html, actual = self._read(session, url)
                    pages += 1
                    if ALBUM_PATH.fullmatch(urlsplit(actual).path):
                        album_pages = [(actual, html)]
                    else:
                        soup = BeautifulSoup(html, "html.parser")
                        album_pages = []
                        # Somente a lista de álbuns do perfil; exclui recomendações laterais.
                        for node in soup.select("#album-list a[href], .album-list a[href], #albums a[href], .album a[href], a.album-link[href], a.album-title[href]"):
                            try:
                                link = page_url(urljoin(actual, node["href"]))
                            except ValueError:
                                continue
                            if ALBUM_PATH.fullmatch(urlsplit(link).path) and link not in albums:
                                album_pages.append((link, None))
                                albums.add(link)
                                if len(albums) >= self.max_albums:
                                    break
                        if not album_pages and not albums:
                            logger.warning("Nenhum álbum encontrado no perfil. Use o link direto /a/ID se o álbum não estiver listado.")
                        for node in soup.select(".pagination a[href], a[rel~=next][href]"):
                            try:
                                link = page_url(urljoin(actual, node["href"]))
                            except ValueError:
                                continue
                            if urlsplit(link).path == urlsplit(root).path and link not in visited and link not in queue:
                                queue.append(link)
                    for album, body in album_pages:
                        if body is None:
                            body, album = self._read(session, album)
                        found = album_items(body, album)
                        if not found:
                            logger.warning("Álbum sem vídeos compatíveis detectados; pode estar vazio, conter só imagens ou ter mudado de formato.")
                        for item in found:
                            if item.content_id in published or item.content_id in seen:
                                continue
                            seen.add(item.content_id)
                            items.append(item)
                            if len(items) >= self.max_items:
                                return items
                    if len(albums) >= self.max_albums:
                        logger.warning("Limite de álbuns consultados atingido; aumente EROME_MAX_ALBUMS se necessário.")
                        break
                if queue:
                    logger.warning("Limite de páginas atingido; aumente EROME_MAX_PAGES se necessário.")
        logger.info("Erome: %d vídeo(s) novo(s) encontrado(s).", len(items))
        return items
