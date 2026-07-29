"""The replay tool is the record's own auditor; lock what it must detect."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

import replay


class TestReplay(unittest.TestCase):
    def test_a_verdict_change_is_detected(self):
        pub = {"z_score": "-2.695", "trembling": "0", "direction": "down", "status": "scoring"}
        same = dict(pub)
        self.assertFalse(replay._differs(pub, same))
        for field, other in (("z_score", "-3.014"), ("trembling", "1"),
                             ("direction", "up"), ("status", "stale")):
            changed = dict(pub, **{field: other})
            self.assertTrue(replay._differs(pub, changed), f"{field} change not detected")

    def test_prose_is_not_part_of_the_verdict(self):
        """source_note is a human note; rewording it must not read as drift."""
        pub = {"z_score": "1.0", "trembling": "0", "direction": "up", "status": "scoring",
               "source_note": "one wording"}
        other = dict(pub, source_note="a different wording")
        self.assertFalse(replay._differs(pub, other))

    def test_the_live_record_replays_since_the_declared_stable_date(self):
        """The real guard: no drift between the collector and the scorer today."""
        import collect
        drifted = []
        for mod in collect.LINES:
            for date, published, replayed in replay.replay_line(mod):
                if date >= replay.STABLE_SINCE and replay._differs(published, replayed):
                    drifted.append((mod.LINE, date))
        self.assertEqual(drifted, [], f"rows since {replay.STABLE_SINCE} do not replay")


if __name__ == "__main__":
    unittest.main()
