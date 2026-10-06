import unittest
from datetime import datetime
from unittest.mock import patch

import requests

from functions import menicka


class MenickaTest(unittest.TestCase):
    def scrape(self, html, status=200):
        response = requests.Response()
        response.status_code = status
        response._content = html.encode('utf-8')
        response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        with patch.dict(menicka.RESTAURANTS, {'Test': 'test'}, clear=True), \
                patch.object(menicka.requests, 'get', return_value=response), \
                patch.object(menicka, 'datetime', create=True) as clock:
            clock.now.return_value = datetime(2026, 10, 6, 10)
            return menicka.scrape_menicka_ceske_budejovice()

    def test_utf8_and_whitespace_before_truncation(self):
        html = '''<meta charset="UTF-8"><div class="menicka">
          <div class="nadpis">Úterý 6.10.2026</div>
          <li class="jidlo"><div class="polozka"><span class="poradi">1.</span>
          150g\t Hovězí\n\t guláš <span>7</span></div></li></div>'''
        self.assertEqual(self.scrape(html), 'Test: Hovězí guláš')

    def test_only_todays_menu(self):
        html = '''<div class="menicka"><div class="nadpis">Pondělí 5.10.2026</div>
          <li class="jidlo"><div class="polozka">Včerejší menu</div></li></div>
          <div class="menicka"><div class="nadpis">Úterý 6.10.2026</div>
          <li class="jidlo"><div class="polozka">Dnešní menu</div></li></div>
          <div class="menicka"><div class="nadpis">Středa 7.10.2026</div>
          <li class="jidlo"><div class="polozka">Zítřejší menu</div></li></div>'''
        self.assertEqual(self.scrape(html), 'Test: Dnešní menu')

    def test_missing_today_does_not_use_tomorrow(self):
        html = '''<div class="menicka"><div class="nadpis">Středa 7.10.2026</div>
          <li class="jidlo"><div class="polozka">Zítřejší menu</div></li></div>'''
        self.assertEqual(self.scrape(html), 'Test: menu není dostupné')

    def test_http_error_is_not_menu(self):
        html = '''<div class="menicka"><div class="nadpis">Úterý 6.10.2026</div>
          <li class="jidlo"><div class="polozka">Chybová stránka</div></li></div>'''
        self.assertIn('Test: Chyba', self.scrape(html, status=503))

    def test_quantity_removal_preserves_initial_letters(self):
        html = '''<meta charset="UTF-8"><div class="menicka"><div class="nadpis">6.10.2026</div>
          <li class="jidlo"><div class="polozka">špenátové noky</div></li>
          <li class="jidlo"><div class="polozka">/1ks Hovězí burger</div></li>
          <li class="polevka"><div class="polozka">0, 25l Kulajda</div></li></div>'''
        self.assertEqual(self.scrape(html), 'Test: špenátové noky | Hovězí burger | Kulajda')


if __name__ == '__main__':
    unittest.main()
