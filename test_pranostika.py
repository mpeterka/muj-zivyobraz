import unittest
from datetime import date
from unittest.mock import patch

from bs4 import BeautifulSoup
from functions.pranostika import get_pranostika_values


class PranostikaTests(unittest.TestCase):
    @patch('functions.pranostika._load_page')
    def test_day_overrides_month_and_removes_reference(self, load):
        load.return_value = BeautifulSoup('''<div class="mw-parser-output">
            <h2><span>Pranostiky pro celý měsíc</span><span>editovat</span></h2><ul><li>Monthly.</li></ul>
            <dl><dt>8. říjen</dt><dd>Daily <a>quote</a>.<sup class="reference">[1]</sup></dd>
            <dt>9. říjen</dt><dd>Wrong day.</dd></dl></div>''', 'html.parser')
        self.assertEqual(get_pranostika_values(date(2026, 10, 8))['pranostika'], 'Daily quote.')

    @patch('functions.pranostika._load_page')
    def test_month_fallback_and_outage(self, load):
        load.return_value = BeautifulSoup('''<div class="mw-parser-output">
            <h2>Pranostiky pro celý měsíc</h2><ul><li>Monthly.</li></ul>
            <h2>Reference</h2><ul><li>Not a quote.</li></ul></div>''', 'html.parser')
        self.assertEqual(get_pranostika_values(date(2026, 10, 8))['pranostika'], 'Monthly.')
        load.return_value = None
        self.assertEqual(get_pranostika_values(date(2026, 10, 8)), {})
