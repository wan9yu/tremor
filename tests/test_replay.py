"""The replay tool is the record's own auditor; lock what it must detect.

Only the tool's LOGIC is tested here, so this file may gate collection. The
actual replay of the committed record lives in audit_record.py and runs after
the commit: committed rows can fail to replay for reasons no new code caused,
and a gate they can fail would halt collection.
"""
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


if __name__ == "__main__":
    unittest.main()
