import unittest
from datetime import date
from unittest.mock import patch

from bs4 import BeautifulSoup
from functions.pranostika import get_pranostika_values

WIKIPEDIA = '''<div class="mw-parser-output"><section><div class="mw-heading mw-heading2"><h2 id="Pranostiky">Pranostiky</h2></div>
    <section><div class="mw-heading mw-heading3"><h3 id="Cesko">Česko</h3></div>
    <ul><li>Brigita svatá na mlhavá rána je bohatá.<sup class="reference">[1]</sup></li>
    <li>O svaté Brigitě bývá mlha na úsvitě.</li></ul></section></section>
    <section><div class="mw-heading mw-heading2"><h2 id="Odkazy">Odkazy</h2></div><ul><li>Not a quote.</li></ul></section></div>'''
WIKIQUOTE = '''<div class="mw-parser-output">
    <h2><span>Pranostiky pro celý měsíc</span><span>editovat</span></h2><ul><li>Monthly.</li></ul>
    <dl><dt>8. říjen</dt><dd>Daily <a>quote</a>.<sup class="reference">[1]</sup></dd>
    <dt>9. říjen</dt><dd>Wrong day.</dd></dl></div>'''
TODAY = date(2026, 10, 8)


def pages(*soups):
    return patch('functions.pranostika._load_page',
                 side_effect=[None if s is None else BeautifulSoup(s, 'html.parser') for s in soups])


class PranostikaTests(unittest.TestCase):
    def test_wikipedia_first_and_shortest(self):
        with pages(WIKIPEDIA) as load:
            values = get_pranostika_values(TODAY)
        self.assertEqual(values, {
            'pranostika': 'O svaté Brigitě bývá mlha na úsvitě.',
            'pranostika_zdroj': 'https://cs.wikipedia.org/wiki/8._%C5%99%C3%ADjen',
            'pranostika_zdroj_nazev': 'Wikipedie'})
        self.assertEqual(load.call_count, 1)

    def test_fallback_to_wikiquote_day_then_month(self):
        empty = '<div class="mw-parser-output"><div class="mw-heading"><h2 id="Pranostiky">x</h2></div><ul><li> </li></ul></div>'
        for first in (None, '<div></div>', empty):
            with pages(first, WIKIQUOTE):
                values = get_pranostika_values(TODAY)
            self.assertEqual(values['pranostika'], 'Daily quote.')
            self.assertEqual(values['pranostika_zdroj_nazev'], 'Wikicitáty')
        monthly = WIKIQUOTE.replace('<dt>8.', '<dt>7.')
        with pages(None, monthly):
            self.assertEqual(get_pranostika_values(TODAY)['pranostika'], 'Monthly.')

    def test_both_sources_down_or_empty(self):
        with pages(None, None):
            self.assertEqual(get_pranostika_values(TODAY), {})
        with pages('<div></div>', '<div class="mw-parser-output"></div>'):
            self.assertEqual(get_pranostika_values(TODAY), {})


if __name__ == '__main__':
    unittest.main()
