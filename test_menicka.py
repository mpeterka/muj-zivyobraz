import unittest
from datetime import datetime
from unittest.mock import patch

import requests

from functions import menicka


class MenickaTest(unittest.TestCase):
    def scrape(self, html, status=200, values=False):
        response = requests.Response()
        response.status_code = status
        response._content = html.encode('utf-8')
        response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        with patch.dict(menicka.RESTAURANTS, {'Test': 'test'}, clear=True), \
                patch.object(menicka.requests, 'get', return_value=response), \
                patch.object(menicka, 'datetime', create=True) as clock:
            clock.now.return_value = datetime(2026, 10, 6, 10)
            if values:
                return menicka.get_menicka_values()
            return menicka.scrape_menicka_ceske_budejovice()

    def test_separate_lines_and_word_boundary_keep_legacy_output(self):
        html = '''<meta charset="UTF-8"><div class="menicka"><div class="nadpis">6.10.2026</div>
          <li class="polevka"><div class="polozka">Hovězí vývar s domácími nudlemi</div></li>
          <li class="jidlo"><div class="polozka">Kuřecí řízek</div></li></div>'''
        values = self.scrape(html, values=True)
        self.assertEqual(values['menicka'], 'Test: Hovězí vývar s domácími n... | Kuřecí řízek')
        self.assertEqual(values['menicka_test'], 'Hovězí vývar s domácími nudlemi\nKuřecí řízek')
        self.assertEqual(values['menicka_1_restaurace'], 'Test')
        self.assertEqual(values['menicka_1_jidla'], values['menicka_test'])
        self.assertEqual(values['menicka_2_restaurace'], '')
        self.assertEqual(values['menicka_2_jidla'], '')
        self.assertEqual(values['menicka_datum'], '6. 10.')
        self.assertEqual(values['menicka_nacteno'], '10:00')

    def test_missing_today_clears_slots_and_reports_unavailable(self):
        values = self.scrape('<div class="menicka"><div class="nadpis">7.10.2026</div></div>', values=True)
        self.assertEqual(values['menicka_test'], '')
        self.assertEqual(values['menicka_1_restaurace'], '')
        self.assertEqual(values['menicka_1_jidla'], '')
        self.assertEqual(values['menicka_stav'], 'Bez nabídky: Test')

    def test_http_error_reports_failure_and_clears_slots(self):
        values = self.scrape('', status=503, values=True)
        self.assertEqual(values['menicka_test'], '')
        self.assertEqual(values['menicka_1_jidla'], '')
        self.assertEqual(values['menicka_stav'], 'Nelze načíst: Test')

    def test_five_dish_bound_and_long_first_word(self):
        html = '<div class="menicka"><div class="nadpis">6.10.2026</div>'
        html += ''.join(f'<li class="jidlo"><div class="polozka">{dish}</div></li>' for dish in (
            'A' * 70 + ' příloha', 'Druhé', 'Třetí', 'Čtvrté', 'Páté', 'Šesté'))
        values = self.scrape(html + '</div>', values=True)
        self.assertEqual(values['menicka_test'], 'A' * 65 + '…\nDruhé\nTřetí\nČtvrté\nPáté')

    def test_longer_dish_keeps_side_and_cuts_only_at_word_boundary(self):
        dish = 'Italské karbanátky s rajčatovou omáčkou a šťouchanými bramborami'
        html = '<meta charset="UTF-8"><div class="menicka"><div class="nadpis">6.10.2026</div>'
        html += f'<li class="jidlo"><div class="polozka">{dish}</div></li></div>'
        self.assertEqual(self.scrape(html, values=True)['menicka_1_jidla'], dish)
        longer = dish + ' a zeleninovým salátem'
        values = self.scrape(html.replace(dish, longer), values=True)
        self.assertEqual(values['menicka_1_jidla'], dish + '…')

    def test_display_slots_skip_unavailable_restaurants(self):
        response = requests.Response()
        response.status_code = 200
        response._content = b'<div class="menicka"><div class="nadpis">6.10.2026</div><li class="jidlo"><div class="polozka">Burger</div></li></div>'
        missing = requests.Response()
        missing.status_code = 200
        missing._content = b''
        with patch.dict(menicka.RESTAURANTS, {'Klika': 'klika', 'Solnice': 'solnice'}, clear=True), \
                patch.object(menicka.requests, 'get', side_effect=[missing, response]), \
                patch.object(menicka, 'datetime') as clock:
            clock.now.return_value = datetime(2026, 10, 6, 10)
            values = menicka.get_menicka_values()
        self.assertEqual(values['menicka_klika'], '')
        self.assertEqual(values['menicka_solnice'], 'Burger')
        self.assertEqual(values['menicka_1_restaurace'], 'Solnice')
        self.assertEqual(values['menicka_1_jidla'], 'Burger')
        self.assertEqual(values['menicka_2_restaurace'], '')
        self.assertEqual(values['menicka_stav'], 'Bez nabídky: Klika')

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
