# Experiment Tracker (exptrack)

A lightweight, reproducible experiment tracker for ML/optimization projects.
Stores runs and metrics in SQLite, supports tags, notes, and basic plotting.

## Features
- Create runs with name, config JSON, tags, notes
- Log metrics (e.g., loss, accuracy, FID) over steps
- List runs, inspect a run, export metrics to CSV
- Plot a metric vs step (optional: matplotlib)

## Install
```bash
pip install -r requirements.txt
