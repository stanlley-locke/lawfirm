#!/usr/bin/env python3
"""Convert JPG/PNG images under static/images/ to WebP for lighter page loads."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is required: pip install Pillow", file=sys.stderr)
    sys.exit(1)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
MAX_WIDTH = 1920
DEFAULT_QUALITY = 82


def convert_image(source: Path, quality: int, max_width: int, dry_run: bool) -> Path | None:
    if source.suffix not in SUPPORTED_EXTENSIONS:
        return None

    target = source.with_suffix(".webp")
    if dry_run:
        print(f"[dry-run] {source} -> {target}")
        return target

    with Image.open(source) as img:
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.getbands() else "RGB")

        width, height = img.size
        if width > max_width:
            ratio = max_width / width
            new_size = (max_width, max(int(height * ratio), 1))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        save_kwargs: dict = {"quality": quality, "method": 6}
        if img.mode == "RGBA":
            save_kwargs["lossless"] = False

        img.save(target, "WEBP", **save_kwargs)

    print(f"Converted: {source.relative_to(source.parents[2])} -> {target.name}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "static" / "images",
        help="Root directory to scan for images",
    )
    parser.add_argument("--quality", type=int, default=DEFAULT_QUALITY)
    parser.add_argument("--max-width", type=int, default=MAX_WIDTH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"Directory not found: {root}", file=sys.stderr)
        return 1

    converted: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix == ".webp":
            continue
        if path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        result = convert_image(path, args.quality, args.max_width, args.dry_run)
        if result:
            converted.append(result)

    print(f"\nTotal converted: {len(converted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
