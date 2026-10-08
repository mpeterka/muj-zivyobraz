import unittest
from unittest.mock import Mock, patch

import requests

from functions import wiki


HISTORY = '''<ul><li>Navigation</li></ul>
<div class="mainpage-block calendar-container">
  <div class="mainpage-headline"><a><span>7</span>. <span>říjen</span> v minulosti</a></div>
  <div class="mainpage-content"><ul>
    <li><span style="visibility:hidden;">0</span>1847 – Česká událost.</li>
    <li>1952 – Další událost (na obrázku).</li>
  </ul><div class="hlist"><ul><li>Další výročí</li></ul></div></div>
</div>'''


class WikiTest(unittest.TestCase):
    def response(self, html):
        response = Mock()
        response.content = html.encode('utf-8')
        response.text = html
        return response

    @patch.object(wiki.requests, 'get')
    def test_history_date_comes_from_content_and_not_today(self, get):
        get.return_value = self.response(HISTORY)
        self.assertEqual(wiki.get_wiki_dnesek_v_minulosti(), {
            'wiki_dnesek_v_minulosti_datum': '7. říjen',
            'wiki_dnesek_v_minulosti': '1847 – Česká událost.\n1952 – Další událost.',
        })

    @patch.object(wiki.requests, 'get')
    def test_history_does_not_publish_partial_or_invalid_content(self, get):
        for html in ('<ul><li>Navigation</li></ul>',
                     HISTORY.replace('7</span>. <span>říjen', '</span><span>'),
                     HISTORY.replace('<li><span style="visibility:hidden;">0</span>1847 – Česká událost.</li>', '').replace('<li>1952 – Další událost (na obrázku).</li>', '')):
            with self.subTest(html=html):
                get.return_value = self.response(html)
                self.assertEqual(wiki.get_wiki_dnesek_v_minulosti(), {})

    @patch.object(wiki.requests, 'get')
    def test_network_failure_preserves_previous_history(self, get):
        get.side_effect = requests.RequestException('offline')
        self.assertEqual(wiki.get_wiki_dnesek_v_minulosti(), {})

    @patch.object(wiki.requests, 'get')
    def test_news_keep_dates_and_remove_references_and_flags(self, get):
        get.return_value = self.response('''<dl><dt>Navigation</dt><dd>Ignore</dd></dl>
        <div class="mw-parser-output"><dl>
        <dt><a>7. října</a> – středa</dt>
        <dd><span class="flagicon"><img alt="Česko"></span>První <a>zpráva</a>.<sup class="reference">[1]</sup></dd>
        <dd>Druhá zpráva.</dd><dt>6. října – úterý</dt><dd>Třetí zpráva.</dd>
        <dd>Čtvrtá zpráva.</dd><dd>Pátá zpráva.</dd><dd>Šestá zpráva.</dd>
        </dl></div>''')
        self.assertEqual(wiki.get_wiki_aktuality(), {'wiki_aktuality':
            '7. října – První zpráva.\n7. října – Druhá zpráva.\n'
            '6. října – Třetí zpráva.'})

    @patch.object(wiki.requests, 'get')
    def test_news_failure_does_not_overwrite_previous_value(self, get):
        get.return_value = self.response('<div class="mw-parser-output"><dl><dt>Navigation</dt><dd>Ignore</dd></dl></div>')
        self.assertEqual(wiki.get_wiki_aktuality(), {})
        get.side_effect = requests.RequestException('offline')
        self.assertEqual(wiki.get_wiki_aktuality(), {})


if __name__ == '__main__':
    unittest.main()
