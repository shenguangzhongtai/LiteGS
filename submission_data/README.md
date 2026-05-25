# LiteGS Experiment Data Package

This directory contains the experiment data prepared for report submission.

Contents:

- `render_results/`: selected qualitative PNG renderings.
- `metrics/`: raw metric values in CSV and JSON format.
- `manifest/manifest.json`: file list and selected-view metadata.

Key metric files:

- `metrics/baseline_metrics.csv`: baseline reproduction results.
- `metrics/improvement_metrics.csv`: improvement and ablation results.
- `metrics/adaptive_density_summary.csv`: compact baseline-vs-adaptive table.
- `metrics/metrics_summary.json`: JSON version containing all recorded metric rows.

The main qualitative comparison figure is:

```text
render_results/render_comparison.png
```

The report source references the copy under:

```text
../report/figures/render_comparison.png
```
