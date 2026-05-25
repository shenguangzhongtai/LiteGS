from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REPORT_FIGURES = ROOT / "report" / "figures"
SUBMISSION = ROOT / "submission_data"
RENDER_RESULTS = SUBMISSION / "render_results"
METRICS = SUBMISSION / "metrics"
MANIFEST = SUBMISSION / "manifest"


SELECTED_VIEWS = {
    "lego": {
        "view_id": "124",
        "baseline_run": "lego_100ep",
        "adaptive_run": "lego_100ep_adaptive",
        "display_size": (260, 260),
    },
    "truck": {
        "view_id": "9",
        "baseline_run": "truck_100ep",
        "adaptive_run": "truck_100ep_adaptive",
        "display_size": (300, 166),
    },
}


def ensure_dirs() -> None:
    for path in (REPORT_FIGURES, RENDER_RESULTS, METRICS, MANIFEST):
        path.mkdir(parents=True, exist_ok=True)


def find_render(run_name: str, view_id: str, suffix: str) -> Path:
    matches = sorted((ROOT / "output" / run_name / "Testset").glob(f"{view_id}-*-{suffix}.png"))
    if not matches:
        raise FileNotFoundError(f"No {suffix} image found for {run_name} view {view_id}")
    return matches[0]


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def fit_image(path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    left = (size[0] - image.width) // 2
    top = (size[1] - image.height) // 2
    canvas.paste(image, (left, top))
    return canvas


def copy_selected_pngs() -> dict[str, dict[str, str]]:
    copied: dict[str, dict[str, str]] = {}
    for scene, spec in SELECTED_VIEWS.items():
        view_id = spec["view_id"]
        baseline = spec["baseline_run"]
        adaptive = spec["adaptive_run"]
        sources = {
            "ground_truth": find_render(baseline, view_id, "gt"),
            "baseline_render": find_render(baseline, view_id, "rd"),
            "adaptive_render": find_render(adaptive, view_id, "rd"),
            "adaptive_ground_truth": find_render(adaptive, view_id, "gt"),
        }
        copied[scene] = {}
        for label, source in sources.items():
            target = RENDER_RESULTS / f"{scene}_{view_id}_{label}.png"
            shutil.copy2(source, target)
            copied[scene][label] = target.relative_to(ROOT).as_posix()
    return copied


def make_render_comparison() -> Path:
    header_font = load_font(24)
    label_font = load_font(21)
    small_font = load_font(18)

    columns = ["Ground Truth", "Baseline", "Adaptive Density"]
    col_width = 320
    left_label_width = 92
    header_h = 52
    row_gap = 24
    row_heights = [SELECTED_VIEWS["lego"]["display_size"][1] + 50, SELECTED_VIEWS["truck"]["display_size"][1] + 50]
    width = left_label_width + col_width * 3
    height = header_h + sum(row_heights) + row_gap + 22
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)

    for idx, title in enumerate(columns):
        x = left_label_width + idx * col_width
        bbox = draw.textbbox((0, 0), title, font=header_font)
        draw.text((x + (col_width - (bbox[2] - bbox[0])) / 2, 15), title, fill=(20, 20, 20), font=header_font)

    y = header_h
    for scene, spec in SELECTED_VIEWS.items():
        view_id = spec["view_id"]
        baseline = spec["baseline_run"]
        adaptive = spec["adaptive_run"]
        display_size = spec["display_size"]
        paths = [
            find_render(baseline, view_id, "gt"),
            find_render(baseline, view_id, "rd"),
            find_render(adaptive, view_id, "rd"),
        ]
        scene_name = scene.capitalize()
        draw.text((14, y + display_size[1] / 2 - 14), scene_name, fill=(20, 20, 20), font=label_font)
        for idx, path in enumerate(paths):
            image = fit_image(path, display_size)
            x = left_label_width + idx * col_width + (col_width - display_size[0]) // 2
            canvas.paste(image, (x, y))
            draw.rectangle((x, y, x + display_size[0] - 1, y + display_size[1] - 1), outline=(190, 190, 190), width=1)
            metric = path.stem.split("-")[1] if "-" in path.stem else ""
            if idx > 0 and metric:
                draw.text((x, y + display_size[1] + 8), f"PSNR {metric} dB", fill=(70, 70, 70), font=small_font)
        y += display_size[1] + 50 + row_gap

    target = REPORT_FIGURES / "render_comparison.png"
    canvas.save(target)
    shutil.copy2(target, RENDER_RESULTS / "render_comparison.png")
    return target


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def make_metrics_summary() -> Path:
    baseline = read_csv(ROOT / "logs" / "baseline_metrics.csv")
    improvements = read_csv(ROOT / "logs" / "improvement_metrics.csv")
    adaptive = read_csv(ROOT / "logs" / "adaptive_density_summary.csv")
    summary = {
        "project": "LiteGS reproduction and adaptive density control",
        "metrics": ["SSIM", "PSNR", "LPIPS"],
        "baseline_rows": baseline,
        "improvement_rows": improvements,
        "adaptive_density_summary": adaptive,
        "selected_views": SELECTED_VIEWS,
    }
    target = METRICS / "metrics_summary.json"
    target.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return target


def make_manifest(copied_pngs: dict[str, dict[str, str]], figure_path: Path, metrics_json: Path) -> Path:
    files = []
    for folder in (RENDER_RESULTS, METRICS):
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                files.append(
                    {
                        "path": path.relative_to(ROOT).as_posix(),
                        "bytes": path.stat().st_size,
                    }
                )
    manifest = {
        "description": "Experiment data package for the LiteGS course report.",
        "render_results": copied_pngs,
        "main_report_figure": figure_path.relative_to(ROOT).as_posix(),
        "metrics_json": metrics_json.relative_to(ROOT).as_posix(),
        "files": files,
    }
    target = MANIFEST / "manifest.json"
    target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return target


def main() -> None:
    ensure_dirs()
    for name in ("baseline_metrics.csv", "improvement_metrics.csv", "adaptive_density_summary.csv"):
        shutil.copy2(ROOT / "logs" / name, METRICS / name)
    copied_pngs = copy_selected_pngs()
    figure_path = make_render_comparison()
    metrics_json = make_metrics_summary()
    manifest = make_manifest(copied_pngs, figure_path, metrics_json)
    print(f"Created {figure_path.relative_to(ROOT)}")
    print(f"Created {metrics_json.relative_to(ROOT)}")
    print(f"Created {manifest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
