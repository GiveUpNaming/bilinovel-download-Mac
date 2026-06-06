import sys
import types
import unittest
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

from backend.bilinovel import browser


class BrowserSelectionTest(unittest.TestCase):
    def test_auto_uses_safari_on_macos(self):
        with patch.object(sys, 'platform', 'darwin'):
            self.assertEqual(browser.resolve_browser_name('auto'), 'safari')

    def test_auto_uses_chromium_on_other_platforms(self):
        with patch.object(sys, 'platform', 'win32'):
            self.assertEqual(browser.resolve_browser_name('auto'), 'chromium')

    def test_explicit_browser_is_case_insensitive(self):
        self.assertEqual(browser.resolve_browser_name('Safari'), 'safari')
        self.assertEqual(browser.resolve_browser_name('CHROMIUM'), 'chromium')

    def test_invalid_browser_is_rejected(self):
        with self.assertRaises(browser.BrowserError):
            browser.resolve_browser_name('firefox')


class BrowserFactoryTest(unittest.TestCase):
    @patch('backend.bilinovel.browser.SafariBrowser')
    def test_factory_creates_safari(self, safari_browser):
        instance = MagicMock()
        safari_browser.return_value = instance

        self.assertIs(browser.create_browser('safari'), instance)
        safari_browser.assert_called_once_with()

    @patch('backend.bilinovel.browser.ChromiumBrowser')
    def test_factory_passes_chromium_path(self, chromium_browser):
        instance = MagicMock()
        chromium_browser.return_value = instance

        result = browser.create_browser('chromium', '/path/to/chrome')

        self.assertIs(result, instance)
        chromium_browser.assert_called_once_with(
            browser_path='/path/to/chrome',
        )


class SafariBrowserTest(unittest.TestCase):
    def test_safari_fetches_and_cleans_html(self):
        driver = MagicMock()
        driver.execute_script.side_effect = [
            '<html>clean</html>',
            'page signature',
        ]
        webdriver = types.SimpleNamespace(Safari=MagicMock(return_value=driver))
        selenium = types.SimpleNamespace(webdriver=webdriver)

        with patch.object(sys, 'platform', 'darwin'):
            with patch.dict(sys.modules, {'selenium': selenium}):
                safari = browser.SafariBrowser()
                html = safari.get_html(
                    'https://www.linovelib.com',
                    clean_hidden_paragraphs=True,
                )
                safari.close()

        self.assertEqual(html, '<html>clean</html>')
        requested_url = driver.get.call_args.args[0]
        parsed_url = urlsplit(requested_url)
        self.assertEqual(
            parsed_url._replace(query='').geturl(),
            'https://www.linovelib.com',
        )
        self.assertIn('bilinovel_cache', parse_qs(parsed_url.query))
        driver.execute_script.assert_any_call(
            browser.HIDDEN_PARAGRAPH_CLEANUP_SCRIPT,
        )
        driver.execute_script.assert_any_call(browser.PAGE_SIGNATURE_SCRIPT)
        driver.quit.assert_called_once_with()

    def test_safari_does_not_modify_non_bilinovel_urls(self):
        url = 'data:text/html,<html></html>'
        self.assertEqual(browser.SafariBrowser._add_cache_buster(url), url)

    def test_safari_accepts_unexpected_alert_and_retries(self):
        class UnexpectedAlertPresentException(Exception):
            pass

        driver = MagicMock()
        driver.execute_script.side_effect = [
            UnexpectedAlertPresentException(),
            '<html>clean</html>',
            'page signature',
        ]
        webdriver = types.SimpleNamespace(Safari=MagicMock(return_value=driver))
        selenium = types.SimpleNamespace(webdriver=webdriver)

        with patch.object(sys, 'platform', 'darwin'):
            with patch.dict(sys.modules, {'selenium': selenium}):
                safari = browser.SafariBrowser()
                html = safari.get_html(
                    'https://www.linovelib.com',
                    clean_hidden_paragraphs=True,
                )

        self.assertEqual(html, '<html>clean</html>')
        driver.switch_to.alert.accept.assert_called_once_with()
        self.assertEqual(driver.execute_script.call_count, 3)

    @patch('backend.bilinovel.browser.time.sleep')
    def test_safari_retries_when_new_url_keeps_old_content(self, sleep):
        driver = MagicMock()
        driver.execute_script.side_effect = [
            '<html>first</html>',
            'first signature',
            '<html>stale</html>',
            'first signature',
            '<html>second</html>',
            'second signature',
        ]
        webdriver = types.SimpleNamespace(Safari=MagicMock(return_value=driver))
        selenium = types.SimpleNamespace(webdriver=webdriver)

        with patch.object(sys, 'platform', 'darwin'):
            with patch.dict(sys.modules, {'selenium': selenium}):
                safari = browser.SafariBrowser()
                safari.get_html(
                    'https://www.linovelib.com/novel/1/1.html',
                    clean_hidden_paragraphs=True,
                )
                html = safari.get_html(
                    'https://www.linovelib.com/novel/1/2.html',
                    clean_hidden_paragraphs=True,
                )

        self.assertEqual(html, '<html>second</html>')
        self.assertEqual(driver.get.call_count, 3)
        sleep.assert_called_once_with(1)

    def test_safari_is_rejected_outside_macos(self):
        with patch.object(sys, 'platform', 'win32'):
            with self.assertRaises(browser.BrowserError):
                browser.SafariBrowser()


if __name__ == '__main__':
    unittest.main()
