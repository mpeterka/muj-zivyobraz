import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch

from functions import detske_prace


class DetskePraceTest(unittest.TestCase):
    def test_rotation_matches_calendar_and_repeats_after_three_weeks(self):
        expected = (
            'Majda · odpadky a podlahy\nMatěj · prádlo\nMarkét · myčka',
            'Majda · myčka\nMatěj · odpadky a podlahy\nMarkét · prádlo',
            'Majda · prádlo\nMatěj · myčka\nMarkét · odpadky a podlahy',
            'Majda · odpadky a podlahy\nMatěj · prádlo\nMarkét · myčka',
        )
        for day, text in zip((5, 12, 19, 26), expected):
            with self.subTest(day=day):
                values = detske_prace.get_detske_prace_values(date(2026, 10, day))
                self.assertEqual(values['detske_prace'], text)
                self.assertEqual(values['detske_prace_nadpis'], 'Služby tento týden')

    def test_services_remain_the_same_through_sunday(self):
        friday = detske_prace.get_detske_prace_values(date(2026, 10, 9))
        self.assertEqual(friday['detske_prace_majda'], 'odpadky a podlahy')
        for day in (10, 11):
            with self.subTest(day=day):
                values = detske_prace.get_detske_prace_values(date(2026, 10, day))
                self.assertEqual(values['detske_prace_nadpis'], 'Služby tento týden')
                self.assertEqual(values['detske_prace_majda'], 'odpadky a podlahy')
                self.assertEqual(values['detske_prace_matej'], 'prádlo')
                self.assertEqual(values['detske_prace_market'], 'myčka')

    def test_rotation_continues_across_year_boundary(self):
        values = detske_prace.get_detske_prace_values(date(2027, 1, 4))
        self.assertEqual(values['detske_prace_majda'], 'myčka')

    def test_changes_on_monday_at_midnight_in_prague(self):
        for month, day, hour, minute, expected in (
                (10, 11, 21, 59, 'odpadky a podlahy'),
                (10, 11, 22, 0, 'myčka'),
                (10, 25, 22, 59, 'prádlo'),
                (10, 25, 23, 0, 'odpadky a podlahy')):
            with self.subTest(month=month, day=day, hour=hour, minute=minute), \
                    patch.object(detske_prace, 'datetime') as clock:
                clock.now.side_effect = lambda tz: datetime(2026, month, day, hour, minute,
                                                           tzinfo=timezone.utc).astimezone(tz)
                values = detske_prace.get_detske_prace_values()
            self.assertEqual(values['detske_prace_nadpis'], 'Služby tento týden')
            self.assertEqual(values['detske_prace_majda'], expected)


if __name__ == '__main__':
    unittest.main()
