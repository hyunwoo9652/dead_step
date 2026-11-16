"""로컬 화면의 API 상태 처리 검증. 실제 브라우저 렌더링은 별도 확인한다."""
import os
import tempfile
import unittest
from unittest.mock import patch

from web_ui import WebState


class WebStateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        env = patch.dict(os.environ, {'LOCALAPPDATA': self.temp_dir.name})
        env.start()
        self.addCleanup(env.stop)
        self.state = WebState()

    def test_hidden_sources_are_only_revealed_after_game(self):
        self.assertEqual(self.state.snapshot()['sources'], [])
        self.state.game.status = 'lost'
        self.assertEqual(len(self.state.snapshot()['sources']), 8)

    def test_scan_and_retry_restore_same_map(self):
        before = self.state.snapshot()
        result = self.state.action({'action': 'scan', 'points': [[14, 0], [14, 1]]})
        self.assertEqual(result['turn'], 1)
        self.assertEqual(len(result['scans']), 2)
        retry = self.state.action({'action': 'retry'})
        self.assertEqual(retry['turn'], 0)
        self.assertEqual(retry['seed'], before['seed'])
        self.assertEqual(retry['walls'], before['walls'])

    def test_flag_does_not_consume_turn(self):
        result = self.state.action({'action': 'flag', 'point': [14, 1]})
        self.assertEqual(result['turn'], 0)
        self.assertIn([14, 1], result['flags'])

    def test_record_is_saved_and_loaded(self):
        self.state.game.turn = 12
        self.state.game.status = 'won'
        self.assertEqual(self.state.snapshot()['record'], 12)
        self.assertEqual(WebState().snapshot()['record'], 12)


if __name__ == '__main__':
    unittest.main()
