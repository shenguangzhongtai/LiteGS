import argparse
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image


def rotmat2qvec(rot):
    rxx, ryx, rzx, rxy, ryy, rzy, rxz, ryz, rzz = rot.flat
    k = np.array(
        [
            [rxx - ryy - rzz, 0, 0, 0],
            [ryx + rxy, ryy - rxx - rzz, 0, 0],
            [rzx + rxz, rzy + ryz, rzz - rxx - ryy, 0],
            [ryz - rzy, rzx - rxz, rxy - ryx, rxx + ryy + rzz],
        ],
        dtype=np.float64,
    ) / 3.0
    eigvals, eigvecs = np.linalg.eigh(k)
    qvec = eigvecs[[3, 0, 1, 2], np.argmax(eigvals)]
    if qvec[0] < 0:
        qvec *= -1
    return qvec


def composite_rgba(src_path, dst_path, background):
    image = Image.open(src_path).convert("RGBA")
    bg_color = (255, 255, 255, 255) if background == "white" else (0, 0, 0, 255)
    canvas = Image.new("RGBA", image.size, bg_color)
    canvas.alpha_composite(image)
    canvas.convert("RGB").save(dst_path)
    return image.size


def frame_to_colmap_pose(frame):
    c2w = np.array(frame["transform_matrix"], dtype=np.float64)
    c2w[:3, 1:3] *= -1.0
    w2c = np.linalg.inv(c2w)
    qvec = rotmat2qvec(w2c[:3, :3])
    tvec = w2c[:3, 3]
    return qvec, tvec


def write_random_ply(path, num_points, seed):
    rng = np.random.default_rng(seed)
    xyz = rng.random((num_points, 3), dtype=np.float32) * 2.6 - 1.3
    rgb = (rng.random((num_points, 3)) * 255).astype(np.uint8)
    with path.open("w", encoding="ascii") as handle:
        handle.write("ply\n")
        handle.write("format ascii 1.0\n")
        handle.write(f"element vertex {num_points}\n")
        handle.write("property float x\n")
        handle.write("property float y\n")
        handle.write("property float z\n")
        handle.write("property float nx\n")
        handle.write("property float ny\n")
        handle.write("property float nz\n")
        handle.write("property uchar red\n")
        handle.write("property uchar green\n")
        handle.write("property uchar blue\n")
        handle.write("end_header\n")
        for point, color in zip(xyz, rgb):
            handle.write(
                f"{point[0]} {point[1]} {point[2]} 0 0 0 "
                f"{int(color[0])} {int(color[1])} {int(color[2])}\n"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Convert a NeRF synthetic scene into the COLMAP-style layout expected by LiteGS."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--background", choices=["white", "black"], default="white")
    parser.add_argument("--train-json", default="transforms_train.json")
    parser.add_argument("--test-json", default="transforms_test.json")
    parser.add_argument("--extension", default=".png")
    parser.add_argument("--random-points", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=3)
    args = parser.parse_args()

    source = args.source.resolve()
    output = (args.output or source.with_name(source.name + "_litegs")).resolve()
    images_dir = output / "images"
    sparse_dir = output / "sparse" / "0"
    images_dir.mkdir(parents=True, exist_ok=True)
    sparse_dir.mkdir(parents=True, exist_ok=True)

    split_specs = [("train", args.train_json), ("test", args.test_json)]
    all_images = []
    split_names = {"train": [], "test": []}
    width = height = None
    fovx = None

    for split, transform_name in split_specs:
        with (source / transform_name).open("r", encoding="utf-8") as handle:
            transforms = json.load(handle)
        fovx = transforms["camera_angle_x"] if fovx is None else fovx
        for frame in transforms["frames"]:
            rel_path = frame["file_path"].lstrip("./")
            src_image = source / f"{rel_path}{args.extension}"
            out_name = f"{split}_{Path(rel_path).name}{args.extension}"
            dst_image = images_dir / out_name
            width, height = composite_rgba(src_image, dst_image, args.background)
            qvec, tvec = frame_to_colmap_pose(frame)
            image_id = len(all_images) + 1
            all_images.append((image_id, qvec, tvec, out_name))
            split_names[split].append(out_name)

    fx = 0.5 * width / math.tan(0.5 * fovx)
    fy = fx
    cx = width * 0.5
    cy = height * 0.5

    with (sparse_dir / "cameras.txt").open("w", encoding="ascii") as handle:
        handle.write("# Camera list with one line of data per camera:\n")
        handle.write("# CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n")
        handle.write("# Number of cameras: 1\n")
        handle.write(f"1 PINHOLE {width} {height} {fx:.12f} {fy:.12f} {cx:.12f} {cy:.12f}\n")

    with (sparse_dir / "images.txt").open("w", encoding="ascii") as handle:
        handle.write("# Image list with two lines of data per image:\n")
        handle.write("# IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n")
        handle.write("# POINTS2D[] as (X, Y, POINT3D_ID)\n")
        handle.write(f"# Number of images: {len(all_images)}, mean observations per image: 0\n")
        for image_id, qvec, tvec, image_name in all_images:
            handle.write(
                f"{image_id} "
                f"{qvec[0]:.17g} {qvec[1]:.17g} {qvec[2]:.17g} {qvec[3]:.17g} "
                f"{tvec[0]:.17g} {tvec[1]:.17g} {tvec[2]:.17g} 1 {image_name}\n\n"
            )

    with (output / "train_test_split.json").open("w", encoding="utf-8") as handle:
        json.dump(split_names, handle, indent=2)

    source_ply = source / "points3d.ply"
    if not source_ply.exists():
        source_ply = source / "lego.ply"
    target_ply = sparse_dir / "points3D.ply"
    if source_ply.exists():
        shutil.copyfile(source_ply, target_ply)
    else:
        write_random_ply(target_ply, args.random_points, args.seed)

    print(f"Prepared LiteGS scene: {output}")
    print(f"Images: {len(all_images)} ({len(split_names['train'])} train, {len(split_names['test'])} test)")
    print(f"Camera: PINHOLE {width}x{height}, fx={fx:.3f}, fy={fy:.3f}")


if __name__ == "__main__":
    main()
