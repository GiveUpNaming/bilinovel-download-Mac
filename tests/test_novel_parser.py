import unittest
from unittest.mock import MagicMock

from backend.bilinovel.Editer import Editer


BILINOVEL_MAIN_HTML = '''
<html><head>
<meta property="og:novel:book_name" content="测试小说">
<meta property="og:novel:author" content="测试作者">
<meta property="og:novel:category" content="测试文库">
<meta property="og:image" content="https://www.bilinovel.com/cover.jpg">
</head><body>
<span class="tag-small-group"><a>奇幻</a><a>冒险</a></span>
<section id="bookSummary"><content>第一行<br>第二行</content></section>
</body></html>
'''

BILINOVEL_CATALOG_HTML = '''
<div class="catalog-volume"><ul class="volume-chapters">
  <li class="chapter-bar chapter-li"><a><h3>测试小说 第一卷</h3></a></li>
  <li class="chapter-li jsChapter"><a href="/novel/1/10.html"><span>序章</span></a></li>
  <li class="chapter-li jsChapter"><a href="/novel/1/11.html"><span>第一章</span></a></li>
</ul></div>
'''


def make_editer():
    editer = Editer.__new__(Editer)
    editer.url_head = 'https://www.bilinovel.com'
    editer.cata_page = 'https://www.bilinovel.com/novel/1/catalog'
    editer.img_url_map = {}
    return editer


class BilinovelParserTest(unittest.TestCase):
    def test_parses_mobile_metadata(self):
        editer = make_editer()

        editer.get_meta_data(BILINOVEL_MAIN_HTML)

        self.assertEqual(editer.book_name, '测试小说')
        self.assertEqual(editer.author, '测试作者')
        self.assertEqual(editer.publisher, '测试文库')
        self.assertEqual(editer.tag_list, ['奇幻', '冒险'])
        self.assertIn('第一行', editer.brief)
        self.assertEqual(
            editer.cover_url_back,
            'https://www.bilinovel.com/cover.jpg',
        )

    def test_parses_mobile_catalog(self):
        editer = make_editer()
        editer.book_name = '测试小说'
        editer.volume_no = 1
        editer.get_html = MagicMock(return_value=BILINOVEL_CATALOG_HTML)

        self.assertTrue(editer.get_index_url())

        self.assertEqual(editer.volume['volume_name'], '第一卷')
        self.assertEqual(editer.volume['chap_names'], ['序章', '第一章'])
        self.assertEqual(
            editer.volume['chap_urls'],
            [
                'https://www.bilinovel.com/novel/1/10.html',
                'https://www.bilinovel.com/novel/1/11.html',
            ],
        )

    def test_parses_mobile_text_and_lazy_images(self):
        editer = make_editer()
        html = '''
        <div id="acontent">
          <p>正文</p>
          <img src="/images/sloading.svg" data-src="https://img3.readpai.com/a.jpg">
          <div id="hidden-images">
            <img src="/images/sloading.svg" data-src="https://img3.readpai.com/b.jpg">
          </div>
        </div>
        '''

        text = editer.get_page_text(html)

        self.assertIn('正文', text)
        self.assertNotIn('sloading.svg', text)
        self.assertIn('../Images/01.jpg', text)
        self.assertEqual(
            list(editer.img_url_map),
            [
                'https://img3.readpai.com/a.jpg',
                'https://img3.readpai.com/b.jpg',
            ],
        )

    def test_removes_advertising_nodes_from_text(self):
        editer = make_editer()
        html = '''
        <div id="acontent">
          <p>前文</p>
          <div class="csgo"><script>advertisement()</script><ins>广告</ins></div>
          <p>后文</p>
        </div>
        '''

        text = editer.get_page_text(html)

        self.assertIn('前文', text)
        self.assertIn('后文', text)
        self.assertNotIn('advertisement', text)
        self.assertNotIn('广告', text)

    def test_parses_mobile_navigation(self):
        editer = make_editer()
        html = "var ReadParams={url_previous:'/novel/1/9.html',url_next:'/novel/1/11.html'}"

        self.assertEqual(
            editer.get_navigation_url(html, 'previous'),
            'https://www.bilinovel.com/novel/1/9.html',
        )
        self.assertEqual(
            editer.get_navigation_url(html, 'next'),
            'https://www.bilinovel.com/novel/1/11.html',
        )


if __name__ == '__main__':
    unittest.main()
