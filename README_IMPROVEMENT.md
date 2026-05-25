# LiteGS Reproduction and Improvement

This repository is based on the original LiteGS codebase:

- Original paper repository: https://github.com/MooreThreads/LiteGS
- Current working branch: `improvement`
- Main improvement: adaptive density control for scene-aware primitive budgeting

For submission, use this `LiteGS/` directory as the code repository root. The outer `2d-gaussian-splatting/` directory is only a local workspace wrapper and is not the project repository root.

If submitting through GitHub, fork the original LiteGS repository first, push this `improvement` branch to your fork, and submit the fork URL plus branch name. The current local `origin` still points to the original repository unless you replace it with your own fork URL.

## Improvement Summary

The final claimed code-level improvement is adaptive density control.

Report mapping:

- Report Section IV, `Identified Limitations`: explains the scene-independent primitive budget and short-run optimization fragility.
- Report Section V, `Proposed Improvements`: describes the scene-aware primitive target and late-stage densification throttling.
- Report Section VI, `Experiments`: compares baseline vs. adaptive density and records negative ablations.
- Report Section VII, `Discussion & Conclusion`: discusses why adaptive density works best on Truck and why other tested ideas failed.

Implemented code changes:

- `litegs/arguments.py`: adds `--adaptive_density`, `--adaptive_density_growth`, `--adaptive_density_min_primitives`, `--adaptive_density_late_start`, and `--adaptive_density_late_interval_scale`.
- `litegs/training/densify.py`: computes a scene-aware target primitive count from the initial point count and slows densification in late training when adaptive mode is enabled.
- `litegs/training/trainer.py`: contains the tested SH warmup option used only as a negative ablation, not as the final claimed improvement.

Final result summary:

- Lego adaptive density: test SSIM improves from `0.8352349` to `0.8527095`, LPIPS improves from `0.1718963` to `0.1711703`, training time drops from about `140s` to `81s`, but PSNR drops from `21.5609226` to `19.6876259`.
- Truck adaptive density: primitive count drops from `988928` to `544256`, while test metrics remain close to baseline: PSNR `28.1873131` to `28.1549969`, SSIM `0.9465371` to `0.9457754`, LPIPS `0.0340067` to `0.0356959`.

Negative ablations kept in logs:

- Scale regularization with `--reg_weight`.
- Edge-gradient consistency variants.
- SH warmup with `--sh_warmup --sh_warmup_interval 20`.

These are not final claimed improvements because they reduce Lego test quality.

## Environment

Tested local environment:

```text
OS: Windows
Conda env: litegs
Python: 3.10
PyTorch: 2.6.0+cu126
CUDA / nvcc: 12.6
```

Python dependencies used by this project:

```text
torchmetrics
plyfile
tqdm
pillow
opencv-python
matplotlib
torchvision
lpips
```

Install project dependencies and LiteGS CUDA extensions from the repository root:

```powershell
conda activate litegs
pip install -r requirement.txt
pip install torchvision lpips
pip install .\litegs\submodules\simple-knn
pip install .\litegs\submodules\fused_ssim
pip install .\litegs\submodules\gaussian_raster
```

On this Windows machine, the CUDA extension setup files were adjusted with `-allow-unsupported-compiler` for the local MSVC/CUDA combination.

## Data Layout

Expected local dataset paths:

```text
data/nerf_synthetic/lego_litegs/
data/tanksandtemples/truck/
```

Scenes used:

- Synthetic scene: NeRF Synthetic Lego, converted to LiteGS/COLMAP-style layout.
- Real scene: Tanks and Temples style Truck, with COLMAP files available under `sparse/0/`.

Large datasets and output folders may be excluded from a Git submission if the course system has a size limit. The required rendered PNGs and raw metrics are also packaged under `submission_data/`.

## One-Line Reproduction Commands

Run from the repository root:

```powershell
cd E:\PySlam\2d-gaussian-splatting\LiteGS; conda activate litegs
```

Original baseline training commands:

```powershell
python example_train.py -s .\data\nerf_synthetic\lego_litegs -i images -m .\output\lego_100ep --eval --iterations 10000 --position_lr_max_steps 10000
```

```powershell
python example_train.py -s .\data\tanksandtemples\truck -i images_2 -m .\output\truck_100ep --eval --resolution 4 --iterations 22000 --position_lr_max_steps 22000
```

Improved adaptive-density training commands:

```powershell
python example_train.py -s .\data\nerf_synthetic\lego_litegs -i images -m .\output\lego_100ep_adaptive --eval --iterations 10000 --position_lr_max_steps 10000 --adaptive_density
```

```powershell
python example_train.py -s .\data\tanksandtemples\truck -i images_2 -m .\output\truck_100ep_adaptive --eval --resolution 4 --iterations 22000 --position_lr_max_steps 22000 --adaptive_density
```

Evaluation commands for baseline:

```powershell
python example_metrics.py -s .\data\nerf_synthetic\lego_litegs -i images -m .\output\lego_100ep --eval --save_image
```

```powershell
python example_metrics.py -s .\data\tanksandtemples\truck -i images_2 -m .\output\truck_100ep --eval --resolution 4 --save_image
```

Evaluation commands for improved runs:

```powershell
python example_metrics.py -s .\data\nerf_synthetic\lego_litegs -i images -m .\output\lego_100ep_adaptive --eval --save_image
```

```powershell
python example_metrics.py -s .\data\tanksandtemples\truck -i images_2 -m .\output\truck_100ep_adaptive --eval --resolution 4 --save_image
```

## Experiment Logs

This project does not use Weights & Biases.

Experiment logs are stored locally in:

```text
logs/
```

Important log files:

```text
logs/baseline_metrics.csv
logs/improvement_metrics.csv
logs/adaptive_density_summary.csv
logs/README.md
```

The final submission data package is stored in:

```text
submission_data/
submission_data/litegs_experiment_data_package.zip
```

It contains:

- Selected PNG renderings and qualitative comparison images under `submission_data/render_results/`.
- Raw metrics in CSV and JSON format under `submission_data/metrics/`.
- A file manifest under `submission_data/manifest/manifest.json`.

## Current Output Folders

Main output folders:

```text
output/lego_100ep/
output/truck_100ep/
output/lego_100ep_adaptive/
output/truck_100ep_adaptive/
```

Additional development or ablation outputs may exist locally but are not required for the final claim.
