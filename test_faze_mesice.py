import unittest
from datetime import date
from unittest.mock import patch

from functions.faze_mesice import faze_mesice


class PhaseTests(unittest.TestCase):
    @patch('functions.faze_mesice.requests.get')
    def test_prague_date_and_dst(self, get):
        get.return_value.json.return_value = {'properties': {'moonphase': 90}}
        result = faze_mesice(date(2026, 10, 25))
        self.assertEqual(result['degrees'], 90)
        self.assertEqual(get.call_args.kwargs['params']['offset'], '+01:00')
        self.assertEqual(get.call_args.kwargs['params']['date'], '2026-10-25')

    @patch('functions.faze_mesice.requests.get')
    def test_invalid_phase(self, get):
        for raw in [float('nan'), float('inf'), 'bad', None]:
            get.return_value.json.return_value = {'properties': {'moonphase': raw}}
            self.assertIsNone(faze_mesice(date(2026, 10, 8)))
