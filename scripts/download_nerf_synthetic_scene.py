import argparse
import json
import pathlib
import time
import urllib.request


REPO = "rishitdagli/nerf-gs-datasets"
TIMEOUT_SECONDS = 60
RETRIES = 5


def download_file(url, out_path):
    tmp_path = out_path.with_suffix(out_path.suffix + ".part")
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
                with tmp_path.open("wb") as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
            tmp_path.replace(out_path)
            return
        except Exception as exc:
            print(f"    retry {attempt}/{RETRIES} after: {exc}")
            if tmp_path.exists():
                tmp_path.unlink()
            if attempt == RETRIES:
                raise
            time.sleep(2 * attempt)


def main():
    parser = argparse.ArgumentParser(description="Download one NeRF Synthetic scene from Hugging Face.")
    parser.add_argument("--scene", required=True, help="Scene name, e.g. lego, chair, drums, ficus.")
    parser.add_argument("--output", type=pathlib.Path, help="Output directory.")
    args = parser.parse_args()

    scene = args.scene.strip("/")
    dest = args.output or pathlib.Path("data") / "nerf_synthetic" / scene

    api = f"https://huggingface.co/api/datasets/{REPO}/tree/main/{scene}?recursive=1"
    print(f"Listing {api}")
    with urllib.request.urlopen(api, timeout=TIMEOUT_SECONDS) as response:
        entries = json.load(response)

    files = [entry for entry in entries if entry.get("type") == "file"]
    if not files:
        raise RuntimeError(f"No files found for scene: {scene}")

    print(f"Files: {len(files)}")
    dest.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    for index, entry in enumerate(files, 1):
        source_path = entry["path"]
        rel_path = source_path[len(scene) + 1 :]
        out_path = dest / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        expected_size = entry.get("size")

        if out_path.exists() and expected_size is not None and out_path.stat().st_size == expected_size:
            skipped += 1
            print(f"[{index}/{len(files)}] skip {rel_path}")
            continue

        url = f"https://huggingface.co/datasets/{REPO}/resolve/main/{source_path}"
        print(f"[{index}/{len(files)}] download {rel_path}")
        download_file(url, out_path)
        downloaded += 1

    print(f"Downloaded: {downloaded}, skipped: {skipped}")
    print(f"Saved to: {dest.resolve()}")


if __name__ == "__main__":
    main()
