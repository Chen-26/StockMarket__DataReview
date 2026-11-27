import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from scripts.archive_snapshot import archive_snapshot


class ArchiveSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "quotes.json"
        self.history = self.root / "history"
        self.snapshot = {
            "updatedAt": "2026-11-30T07:10:00+00:00",
            "provider": "fixture",
            "quotes": [{"symbol": str(i)} for i in range(8)],
            "emotion": {
                "tradeDate": "2026-11-30",
                "breadth": {"total": 4300},
                "pools": {"limitUpCount": 12},
            },
        }
        self.source.write_text(json.dumps(self.snapshot), encoding="utf-8")
        self.after_close = dt.datetime(2026, 11, 30, 15, 10, tzinfo=dt.timezone(dt.timedelta(hours=8)))

    def tearDown(self):
        self.temp.cleanup()

    def test_archives_one_snapshot_and_writes_date_index(self):
        first = archive_snapshot(self.source, self.history, self.after_close)
        self.assertEqual(first.name, "2026-11-30.json")
        self.snapshot["updatedAt"] = "later update"
        self.source.write_text(json.dumps(self.snapshot), encoding="utf-8")
        archive_snapshot(self.source, self.history, self.after_close)
        archived = json.loads(first.read_text(encoding="utf-8"))
        index = json.loads((self.history / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(archived["updatedAt"], "2026-11-30T07:10:00+00:00")
        self.assertEqual(index["dates"], ["2026-11-30"])

    def test_does_not_archive_before_close_or_when_snapshot_is_incomplete(self):
        before_close = self.after_close.replace(hour=14, minute=59)
        self.assertIsNone(archive_snapshot(self.source, self.history, before_close))
        incomplete = {**self.snapshot, "quotes": [{"symbol": "one"}]}
        self.source.write_text(json.dumps(incomplete), encoding="utf-8")
        self.assertIsNone(archive_snapshot(self.source, self.history, self.after_close))
        self.assertFalse(self.history.exists())


if __name__ == "__main__":
    unittest.main()
