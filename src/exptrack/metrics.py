from __future__ import annotations

import csv
from typing import Iterable, Tuple


def export_series_to_csv(series: list[tuple[int, float]], out_path: str) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["step", "value"])
        for step, value in series:
            w.writerow([step, value])


def simple_moving_average(series: list[tuple[int, float]], window: int = 5) -> list[tuple[int, float]]:
    if window <= 1:
        return series[:]
    out: list[tuple[int, float]] = []
    values = [v for _, v in series]
    steps = [s for s, _ in series]
    for i in range(len(series)):
        lo = max(0, i - window + 1)
        chunk = values[lo : i + 1]
        out.append((steps[i], sum(chunk) / len(chunk)))
    return out
