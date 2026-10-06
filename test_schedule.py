import os
import unittest
from contextlib import ExitStack
from datetime import datetime, timezone
from unittest.mock import patch

os.environ.setdefault('IMPORT_KEY', 'test-only')
import main


class MenuScheduleTest(unittest.TestCase):
    def test_updates_during_lunch_preparation_in_summer_and_winter(self):
        with ExitStack() as stack:
            stack.enter_context(patch.object(main.signal, 'SIGUSR1', 10, create=True))
            stack.enter_context(patch.object(main.signal, 'signal'))
            stack.enter_context(patch.object(main.signal, 'pause', create=True))
            stack.enter_context(patch.object(main.BackgroundScheduler, 'start'))
            for name in vars(main):
                if name.startswith('job_'):
                    stack.enter_context(patch.object(main, name))
            with self.assertLogs(level='INFO'):
                main.main()
        trigger = main.scheduler.get_job('menicka').trigger
        for month, utc_hour in ((7, 6), (12, 7)):
            now = datetime(2026, month, 6, utc_hour, 30, tzinfo=timezone.utc)
            next_time = trigger.get_next_fire_time(None, now)
            self.assertEqual(next_time.hour, 9)
            self.assertEqual(next_time.minute, 0)
            self.assertEqual(next_time.tzinfo.zone, 'Europe/Prague')
        now = datetime(2026, 7, 6, 12, 1, tzinfo=timezone.utc)
        self.assertEqual(trigger.get_next_fire_time(None, now).hour, 18)


if __name__ == '__main__':
    unittest.main()
