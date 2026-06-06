import os
import sys
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


HIDDEN_PARAGRAPH_CLEANUP_SCRIPT = """
const paragraphs = Array.from(document.querySelectorAll('p'));
const hiddenMarkers = [];

for (const paragraph of paragraphs) {
    if (window.getComputedStyle(paragraph).display === 'none') {
        for (const attribute of Array.from(paragraph.attributes)) {
            if (attribute.name.startsWith('data-')) {
                hiddenMarkers.push([attribute.name, attribute.value]);
            }
        }
    }
}

for (const paragraph of paragraphs) {
    const hasHiddenMarker = hiddenMarkers.some(
        ([name, value]) => paragraph.getAttribute(name) === value
    );
    if (window.getComputedStyle(paragraph).display === 'none' || hasHiddenMarker) {
        paragraph.remove();
        continue;
    }

    for (const attribute of Array.from(paragraph.attributes)) {
        if (attribute.name.startsWith('data-')) {
            paragraph.removeAttribute(attribute.name);
        }
    }
}
return document.documentElement.outerHTML;
"""

PAGE_SIGNATURE_SCRIPT = """
const content = document.querySelector('#TextContent') || document.body;
return `${document.title}\n${content ? content.innerText : ''}`;
"""


class BrowserError(RuntimeError):
    pass


def resolve_browser_name(browser_name):
    name = (browser_name or 'auto').strip().lower()
    if name == 'auto':
        return 'safari' if sys.platform == 'darwin' else 'chromium'
    if name not in ('safari', 'chromium'):
        raise BrowserError('浏览器类型必须是 auto、safari 或 chromium')
    return name


class SafariBrowser:
    def __init__(self):
        if sys.platform != 'darwin':
            raise BrowserError('Safari 浏览器后端只能在 macOS 上使用')

        try:
            from selenium import webdriver
        except ImportError as exc:
            raise BrowserError(
                '缺少 Selenium。请先运行 pip install -r requirements.txt'
            ) from exc

        try:
            self.driver = webdriver.Safari()
            self._last_content_path = None
            self._last_content_signature = None
        except Exception as exc:
            raise BrowserError(
                'Safari 启动失败。请打开 Safari 设置的“开发者”部分，'
                '启用“允许远程自动化”，或在终端运行 safaridriver --enable'
            ) from exc

    def get_html(self, url, clean_hidden_paragraphs=False):
        target_path = urlsplit(url).path
        attempts = 7 if clean_hidden_paragraphs else 1
        html = None

        for attempt in range(attempts):
            fresh_url = self._add_cache_buster(url)
            self._run_with_alert_handling(lambda: self.driver.get(fresh_url))
            if not clean_hidden_paragraphs:
                return self._run_with_alert_handling(
                    lambda: self.driver.page_source
                )

            html = self._run_with_alert_handling(
                lambda: self.driver.execute_script(
                    HIDDEN_PARAGRAPH_CLEANUP_SCRIPT
                )
            )
            signature = self._run_with_alert_handling(
                lambda: self.driver.execute_script(PAGE_SIGNATURE_SCRIPT)
            )
            is_stale = (
                self._last_content_path is not None
                and target_path != self._last_content_path
                and signature == self._last_content_signature
            )
            if not is_stale:
                self._last_content_path = target_path
                self._last_content_signature = signature
                return html
            if attempt < attempts - 1:
                time.sleep(min(2 ** attempt, 8))

        raise BrowserError(
            f'Safari 未能刷新章节正文：{url}。请稍后重试或增加下载间隔'
        )

    @staticmethod
    def _add_cache_buster(url):
        parsed = urlsplit(url)
        if not parsed.hostname or not parsed.hostname.endswith('linovelib.com'):
            return url

        query = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key != 'bilinovel_cache'
        ]
        query.append(('bilinovel_cache', str(time.time_ns())))
        return urlunsplit(parsed._replace(query=urlencode(query)))

    def _run_with_alert_handling(self, action):
        for _ in range(3):
            try:
                return action()
            except Exception as exc:
                if exc.__class__.__name__ != 'UnexpectedAlertPresentException':
                    raise
                try:
                    self.driver.switch_to.alert.accept()
                except Exception:
                    pass
        return action()

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass


class ChromiumBrowser:
    def __init__(self, browser_path=None):
        try:
            from DrissionPage import Chromium, ChromiumOptions
        except ImportError as exc:
            raise BrowserError(
                '缺少 DrissionPage。请先运行 pip install -r requirements.txt'
            ) from exc

        options = ChromiumOptions()
        path = browser_path or self._default_browser_path()
        if path:
            options.set_browser_path(path)

        try:
            self.browser = Chromium(options)
            self.tab = self.browser.latest_tab
        except Exception as exc:
            raise BrowserError(
                'Chromium 浏览器启动失败，请确认已安装 Chrome 或 Edge，'
                '或通过 --browser-path 指定浏览器可执行文件'
            ) from exc

    @staticmethod
    def _default_browser_path():
        if sys.platform != 'win32':
            return None

        candidates = (
            r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
            r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        )
        return next((path for path in candidates if os.path.exists(path)), None)

    def get_html(self, url, clean_hidden_paragraphs=False):
        self.tab.get(url)
        if clean_hidden_paragraphs:
            html = self.tab.run_js(HIDDEN_PARAGRAPH_CLEANUP_SCRIPT)
            if html:
                return html
        return self.tab.html

    def close(self):
        try:
            self.browser.quit()
        except Exception:
            pass


def create_browser(browser_name='auto', browser_path=None):
    resolved_name = resolve_browser_name(browser_name)
    if resolved_name == 'safari':
        return SafariBrowser()
    return ChromiumBrowser(browser_path=browser_path)
