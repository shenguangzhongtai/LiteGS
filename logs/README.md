# Experiment Logs

This directory stores local experiment logs and metric summaries for the LiteGS course project.

Weights & Biases is not used in this project. The report should cite this local directory as the experiment log location.

Current files:

- `baseline_metrics.csv`: baseline reproduction metrics collected so far.
- `improvement_metrics.csv`: improvement and ablation metrics collected during the improvement stage.
- `adaptive_density_summary.csv`: compact baseline-vs-adaptive table for the report.

Current status:

- Lego 50-epoch and 100-epoch baseline metrics have been recorded.
- Truck 100-epoch baseline metrics have been recorded.
- Scale-regularization ablations on Lego have been recorded. Both `reg_weight=0.0001` and `reg_weight=0.00001` reduce quality compared with the baseline, so this direction is currently treated as a negative ablation rather than a final improvement.
- Adaptive density control on Lego has been recorded. It reduces training time from about 140s to 81s and slightly improves test SSIM/LPIPS, while PSNR decreases.
- Adaptive density control on Truck has been recorded. It reduces the output point cloud from 988928 to 544256 primitives, while test PSNR changes only from 28.1873 to 28.1550.
- Edge-aware gradient consistency on Lego has been recorded. Global, weaker late, and masked edge variants all reduce test quality compared with the baseline, so this direction is treated as a negative ablation rather than a final improvement.
- SH warmup on Lego has been recorded with `sh_warmup_interval=20`. It reduces test quality compared with the baseline, so this setting is treated as a negative ablation rather than a final improvement.

Recommended report wording:

```text
All experiment logs and metric summaries are saved under the repository-local logs/ directory. We did not use wandb for this lightweight course reproduction.
```
