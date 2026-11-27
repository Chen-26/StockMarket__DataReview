#!/usr/bin/env python3
"""Keep one end-of-day market snapshot per trading session."""
import argparse
import datetime as dt
import json
from pathlib import Path

SHANGHAI = dt.timezone(dt.timedelta(hours=8))
RETENTION_SESSIONS = 756


def archive_snapshot(snapshot_path, history_dir, now=None):
    now = now or dt.datetime.now(SHANGHAI)
    snapshot = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    emotion = snapshot.get("emotion") or {}
    pools = emotion.get("pools") or {}
    breadth = emotion.get("breadth") or {}
    trade_date = emotion.get("tradeDate")
    if not trade_date:
        raise ValueError("snapshot is missing emotion.tradeDate")
    session = dt.datetime.strptime(trade_date, "%Y-%m-%d").date()
    if session.weekday() >= 5 or now.date() < session:
        return None
    if now.date() == session and now.time() < dt.time(15, 5):
        return None
    if not snapshot.get("quotes") or len(snapshot["quotes"]) < 8:
        return None
    if not breadth.get("total") or not pools.get("limitUpCount"):
        return None

    folder = Path(history_dir)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (session.isoformat() + ".json")
    if not target.exists():
        target.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    files = sorted(folder.glob("????-??-??.json"))
    for old in files[:-RETENTION_SESSIONS]:
        old.unlink()
    dates = [path.stem for path in sorted(folder.glob("????-??-??.json"))]
    index = {"dates": dates, "oldest": dates[0] if dates else None, "latest": dates[-1] if dates else None}
    (folder / "index.json").write_text(json.dumps(index, separators=(",", ":")) + "\n", encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", default="public/data/quotes.json")
    parser.add_argument("--history-dir", default="data/history")
    args = parser.parse_args()
    archived = archive_snapshot(args.snapshot, args.history_dir)
    if archived:
        print("Archived {}".format(archived))
    else:
        print("No end-of-day trading snapshot archived")


if __name__ == "__main__":
    main()
