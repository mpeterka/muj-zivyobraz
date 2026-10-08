import unittest
from unittest.mock import patch

from functions import fortunes


class FortunesTest(unittest.TestCase):
    def test_plihal_tabs_become_one_space_and_keep_verse_lines(self):
        with patch.object(fortunes.random, 'choice', side_effect=lambda quotes: next(
                quote for quote in quotes if quote.startswith('Sedím v kanceláři'))):
            text = fortunes.plihal()['plihal']

        self.assertNotIn('\t', text)
        self.assertTrue(text.startswith(
            'Sedím v kanceláři\n'
            'a dívám se z okna na jaro. Nejsem krysa, jsem pařez.\n'
            'Je jaro. Kancelářský pařez.\n'))
        self.assertIn('\nŠéf vedle mě dřímá. Šéf taky obrůstá mechem.\n', text)
        self.assertTrue(text.endswith('-- Karel Plíhal: Jaro'))


if __name__ == '__main__':
    unittest.main()
