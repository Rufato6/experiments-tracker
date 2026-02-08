from __future__ import annotations

import argparse
import json
import sys

from exptrack.db import ExperimentDB
from exptrack.metrics import export_series_to_csv, simple_moving_average


def cmd_init(args) -> int:
    db = ExperimentDB(args.db)
    db.init()
    print(f"[OK] Initialized database: {args.db}")
    return 0


def cmd_run_create(args) -> int:
    db = ExperimentDB(args.db)
    db.init()
    config = json.loads(args.config) if args.config else {}
    run_id = db.create_run(name=args.name, tags=args.tags or "", notes=args.notes or "", config=config)
    print(f"[OK] Created run id={run_id} name={args.name}")
    return 0


def cmd_run_list(args) -> int:
    db = ExperimentDB(args.db)
    db.init()
    runs = db.list_runs(limit=args.limit)
    if not runs:
        print("(no runs)")
        return 0
    for r in runs:
        print(f"- id={r.id} | {r.created_at} | {r.name} | tags={r.tags}")
    return 0


def cmd_run_show(args) -> int:
    db = ExperimentDB(args.db)
    db.init()
    r = db.get_run(args.run)
    if not r:
        print("[ERR] Run not found")
        return 2
    print(f"id: {r.id}")
    print(f"name: {r.name}")
    print(f"created_at: {r.created_at}")
    print(f"tags: {r.tags}")
    print(f"notes: {r.notes}")
    print(f"config_json: {r.config_json}")
    names = db.list_metric_names(r.id)
    print(f"metrics: {', '.join(names) if names else '(none)'}")
    return 0


def cmd_run_delete(args) -> int:
    db = ExperimentDB(args.db)
    db.init()
    ok = db.delete_run(args.run)
    print("[OK] deleted" if ok else "[ERR] run not found")
    return 0 if ok else 2


def cmd_metric_log(args) -> int:
    db = ExperimentDB(args.db)
    db.init()
    if not db.get_run(args.run):
        print("[ERR] Run not found")
        return 2
    mid = db.log_metric(args.run, args.name, args.step, args.value)
    print(f"[OK] metric_id={mid} run={args.run} {args.name}@{args.step}={args.value}")
    return 0


def cmd_metric_export(args) -> int:
    db = ExperimentDB(args.db)
    db.init()
    series = db.get_metric_series(args.run, args.name)
    if not series:
        print("[ERR] No data for that metric.")
        return 2
    export_series_to_csv(series, args.out)
    print(f"[OK] Exported to {args.out}")
    return 0


def cmd_metric_plot(args) -> int:
    db = ExperimentDB(args.db)
    db.init()
    series = db.get_metric_series(args.run, args.name)
    if not series:
        print("[ERR] No data for that metric.")
        return 2

    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("[ERR] matplotlib not installed. Install: pip install matplotlib")
        return 2

    if args.sma > 1:
        series_s = simple_moving_average(series, window=args.sma)
    else:
        series_s = series

    xs = [s for s, _ in series_s]
    ys = [v for _, v in series_s]

    plt.figure()
    plt.plot(xs, ys)
    plt.title(f"run={args.run} metric={args.name}")
    plt.xlabel("step")
    plt.ylabel("value")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="exptrack", description="Minimal experiment tracker (SQLite)")
    p.add_argument("--db", default="exptrack.db", help="Path to SQLite DB file")

    sub = p.add_subparsers(dest="cmd", required=True)

    # init
    sp = sub.add_parser("init", help="Initialize database")
    sp.set_defaults(fn=cmd_init)

    # run
    runp = sub.add_parser("run", help="Run operations")
    runsub = runp.add_subparsers(dest="run_cmd", required=True)

    sp = runsub.add_parser("create", help="Create a new run")
    sp.add_argument("--name", required=True)
    sp.add_argument("--tags", default="")
    sp.add_argument("--notes", default="")
    sp.add_argument("--config", default="{}", help="JSON string with config (e.g. '{\"epochs\":100}')")
    sp.set_defaults(fn=cmd_run_create)

    sp = runsub.add_parser("list", help="List runs")
    sp.add_argument("--limit", type=int, default=50)
    sp.set_defaults(fn=cmd_run_list)

    sp = runsub.add_parser("show", help="Show run details")
    sp.add_argument("--run", type=int, required=True)
    sp.set_defaults(fn=cmd_run_show)

    sp = runsub.add_parser("delete", help="Delete a run")
    sp.add_argument("--run", type=int, required=True)
    sp.set_defaults(fn=cmd_run_delete)

    # metric
    mp = sub.add_parser("metric", help="Metric operations")
    msub = mp.add_subparsers(dest="metric_cmd", required=True)

    sp = msub.add_parser("log", help="Log a metric point")
    sp.add_argument("--run", type=int, required=True)
    sp.add_argument("--name", required=True)
    sp.add_argument("--step", type=int, required=True)
    sp.add_argument("--value", type=float, required=True)
    sp.set_defaults(fn=cmd_metric_log)

    sp = msub.add_parser("export", help="Export a metric series to CSV")
    sp.add_argument("--run", type=int, required=True)
    sp.add_argument("--name", required=True)
    sp.add_argument("--out", required=True)
    sp.set_defaults(fn=cmd_metric_export)

    sp = msub.add_parser("plot", help="Plot a metric series")
    sp.add_argument("--run", type=int, required=True)
    sp.add_argument("--name", required=True)
    sp.add_argument("--sma", type=int, default=1, help="Simple moving average window")
    sp.set_defaults(fn=cmd_metric_plot)

    return p


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = build_parser()
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
