import importlib
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

checkin = importlib.import_module('swu_checkin.check_in')
from swu_checkin.runner import may_submit


class ReliabilityTests(unittest.TestCase):
    def context(self):
        ctx = Mock()
        ctx.transition = {'id': 'task1', 'formId': 'form1'}
        ctx.student_id = 'test'
        ctx.latitude = 1
        ctx.longitude = 1
        ctx.building = 'test'
        ctx.room = 'test'
        return ctx

    @patch.object(checkin.time, 'sleep')
    @patch.object(checkin.requests, 'post')
    def test_http_200_does_not_prove_checkin(self, post, sleep):
        with patch.object(checkin, 'get_transition_today', return_value={'id': 'task1', 'formId': 'form1', 'qdzt': '未签到'}):
            self.assertEqual(checkin._submit_checkin(self.context(), 10), 4)

    @patch.object(checkin.time, 'sleep')
    @patch.object(checkin.requests, 'post')
    def test_other_task_cannot_confirm_submission(self, post, sleep):
        with patch.object(checkin, 'get_transition_today', return_value={'id': 'task2', 'formId': 'form1', 'qdzt': '已签到'}):
            self.assertEqual(checkin._submit_checkin(self.context(), 10), 4)

    @patch.object(checkin.time, 'sleep')
    @patch.object(checkin.requests, 'post')
    def test_same_task_confirmed_after_delay(self, post, sleep):
        with patch.object(checkin, 'get_transition_today', side_effect=[None, {'id': 'task1', 'formId': 'form1', 'qdzt': '已签到'}]):
            self.assertEqual(checkin._submit_checkin(self.context(), 10), 1)

    def test_cross_day_and_window_limits(self):
        self.assertTrue(may_submit(datetime.fromisoformat('2026-10-17T21:10:00+08:00'), '2026-10-17'))
        self.assertFalse(may_submit(datetime.fromisoformat('2026-10-18T01:10:00+08:00'), '2026-10-17'))
        self.assertFalse(may_submit(datetime.fromisoformat('2026-10-17T21:10:00+08:00'), '2026-10-16'))
        self.assertFalse(may_submit(datetime.fromisoformat('2026-10-17T23:25:00+08:00'), '2026-10-17'))


if __name__ == '__main__':
    unittest.main()

