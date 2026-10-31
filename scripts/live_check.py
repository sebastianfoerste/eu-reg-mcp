"""Check the live observatory data the server reads: reachable, parseable, fresh.

Exits non-zero when the snapshot cannot be loaded, has no fetched register,
or is older than register.STALE_AFTER_DAYS. Used by the weekly workflow.
"""

from __future__ import annotations

import sys

from eu_reg_mcp import data, register

OBSERVATORY_ACTIONS = (
    "https://github.com/sebastianfoerste/micar-register-observatory/actions"
)


def main() -> int:
    snapshot = data.load_snapshot()
    changelog = data.load_changelog()
    summary = register.summarize(snapshot)
    fetched = [r for r in summary["registers"] if r["fetched"]]
    print(
        f"snapshot {summary['snapshot_date']} "
        f"(age {summary['data_age_days']} days), "
        f"{len(fetched)}/{len(summary['registers'])} registers fetched, "
        f"{sum(r['entries'] for r in fetched)} entries, "
        f"{len(changelog)} changelog records"
    )
    if not fetched:
        print("FAIL: no register was fetched in the latest snapshot")
        return 1
    if summary["stale"] is None:
        print(
            f"FAIL: snapshot date {summary['snapshot_date']!r} is missing or "
            f"unparsable, so its age cannot be checked against the "
            f"{register.STALE_AFTER_DAYS}-day threshold. See {OBSERVATORY_ACTIONS}"
        )
        return 1
    if summary["stale"]:
        print(
            f"FAIL: snapshot {summary['snapshot_date']} is "
            f"{summary['data_age_days']} days old; the threshold is "
            f"{register.STALE_AFTER_DAYS} days, so a weekly observatory refresh "
            f"was missed. See {OBSERVATORY_ACTIONS}"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
