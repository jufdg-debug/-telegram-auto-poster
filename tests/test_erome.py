"""Fixtures sintéticas: nenhum acesso a mídia real nem envio ao Telegram."""
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import main
from sources.erome_source import EromeSource, album_items, page_url

ALBUM = "https://www.erome.com/a/Test1"
HTML = '''<h1>Meu vídeo &amp; teste</h1><div class="media-group" id="v1">
<video><source src="https://s1.erome.com/abc/video.mp4?sig=old">
<source src="https://s1.erome.com/abc/video-low.mp4"></video></div>
<div class="media-group" id="pic"><img src="https://s1.erome.com/pic.jpg"></div>'''


class EromeTests(unittest.TestCase):
    def test_one_video_per_player_and_no_images(self):
        items = album_items(HTML, ALBUM)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Meu vídeo & teste")
        self.assertIn("video.mp4", items[0].media_url)

    def test_stable_id_when_signature_host_or_order_changes(self):
        first = album_items(HTML, ALBUM)[0]
        updated = HTML.replace("sig=old", "sig=new").replace("s1.erome", "s9.erome")
        self.assertEqual(first.content_id, album_items(updated, ALBUM)[0].content_id)

    def test_reject_external_media_and_non_video(self):
        for target in ("https://evil.example/video.mp4", "http://s1.erome.com/x.mp4", "https://erome.com.evil.example/x.mp4", "https://s1.erome.com/x.jpg"):
            self.assertEqual(album_items(f'<video src="{target}"></video>', ALBUM), [])

    def test_page_validation_and_own_posts(self):
        self.assertEqual(page_url("https://erome.com/User?t=reposts"), "https://www.erome.com/User?t=posts")
        for url in ("http://erome.com/User", "https://example.org/a/X", "https://www.erome.com/login", "https://www.erome.com/search?q=test", "https://u:p@www.erome.com/a/X"):
            with self.assertRaises(ValueError):
                page_url(url)

    @patch("sources.erome_source.get_published_ids")
    def test_pagination_skips_published_before_limit(self, published):
        published.return_value = {album_items(HTML, ALBUM)[0].content_id}
        root = page_url("https://www.erome.com/User")
        page2 = page_url("https://www.erome.com/User?page=2")
        second = "https://www.erome.com/a/Test2"
        pages = {
            root: '<div id="album-list"><a href="/a/Test1">a</a></div><div class="pagination"><a href="/User?page=2">2</a></div><aside><a href="/a/Unrelated">Recommendation</a></aside>',
            ALBUM: HTML,
            page2: '<div id="album-list"><a href="/a/Test2">b</a></div>',
            second: HTML,
        }
        source = EromeSource({"urls": [root], "max_items": 1})
        with patch.object(source, "_read", side_effect=lambda session, url: (pages[url], url)) as read:
            items = source.fetch_new_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].page_url, second)
        self.assertEqual(read.call_count, 4)

    @patch("sources.erome_source.get_published_ids", return_value=set())
    def test_overlapping_album_and_profile_do_not_duplicate(self, published):
        root = page_url("https://www.erome.com/User")
        source = EromeSource({"urls": [ALBUM, root], "max_items": 10})
        pages = {ALBUM: HTML, root: '<div id="album-list"><a href="/a/Test1">a</a></div>'}
        with patch.object(source, "_read", side_effect=lambda session, url: (pages[url], url)):
            self.assertEqual(len(source.fetch_new_items()), 1)

    def test_block_and_redirect_stop(self):
        source = EromeSource({"urls": [ALBUM]})
        session = MagicMock()
        response = session.get.return_value.__enter__.return_value
        response.is_redirect = False
        response.status_code = 403
        with self.assertRaises(RuntimeError):
            source._read(session, ALBUM)
        response.is_redirect = True
        response.headers = {"Location": "https://example.org/private"}
        with self.assertRaises(ValueError):
            source._read(session, ALBUM)

    @patch("main.requests.get")
    @patch("main.requests.head")
    def test_download_referer_and_html_rejection(self, head, get):
        head.return_value.headers = {}
        response = get.return_value.__enter__.return_value
        response.is_redirect = False
        response.headers = {"Content-Type": "text/html"}
        item = album_items(HTML, ALBUM)[0]
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(main.download_video(item, directory))
        self.assertEqual(get.call_args.kwargs["headers"]["Referer"], ALBUM)
        self.assertFalse(get.call_args.kwargs["allow_redirects"])

    @patch("main.mark_published")
    @patch("main.send_video")
    @patch("main.download_video")
    @patch("main.is_published", return_value=False)
    def test_dry_run_never_downloads_sends_or_records(self, published, download, send, mark):
        with patch.object(main, "DRY_RUN", True):
            self.assertTrue(main.process_item(album_items(HTML, ALBUM)[0], "Erome"))
        download.assert_not_called()
        send.assert_not_called()
        mark.assert_not_called()


if __name__ == "__main__":
    unittest.main()
