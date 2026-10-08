import unittest
from datetime import date
from unittest.mock import patch, Mock

from functions.slunce import get_slunce_zitra_values


class SlunceTests(unittest.TestCase):
    @patch('functions.slunce.requests.get')
    def test_tomorrow_and_prague_clock_change(self, get):
        get.return_value.json.return_value = {'properties': {
            'sunrise': {'time': '2026-10-25T05:39:00Z'},
            'sunset': {'time': '2026-10-25T15:50:00Z'},
        }}
        self.assertEqual(get_slunce_zitra_values(date(2026, 10, 24)), {
            'slunce_zitra_vychod': '6:39', 'slunce_zitra_zapad': '16:50',
            'slunce_zitra_datum': '25. 10.',
        })
        self.assertEqual(get.call_args.kwargs['params']['date'], '2026-10-25')
        self.assertEqual(get.call_args.kwargs['params']['offset'], '+01:00')

    @patch('functions.slunce.requests.get')
    def test_invalid_payload_does_not_publish(self, get):
        get.return_value.json.return_value = {'properties': {}}
        self.assertIsNone(get_slunce_zitra_values(date(2026, 10, 8)))


if __name__ == '__main__':
    unittest.main()
