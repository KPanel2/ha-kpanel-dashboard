#!/usr/bin/env python3
"""Regenerate HA brand images from the KPanel2 brand_kit logo.

Usage (from this repo, when checked out as a kpanel2 submodule)::

    python3 scripts/sync_brand_from_kit.py

Or with an explicit source::

    python3 scripts/sync_brand_from_kit.py --source /path/to/brand_kit/logo.png

Requires Pillow. Outputs into custom_components/kpanel_dashboard/brand/ for
Home Assistant 2026.3+ local brands proxy, plus images/logo.png for the README.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow is required: pip install pillow") from exc

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_BRAND = REPO_ROOT / "custom_components" / "kpanel_dashboard" / "brand"
DEFAULT_OUT_README = REPO_ROOT / "images" / "logo.png"
MONOREPO_KIT = REPO_ROOT.parents[1] / "brand_kit" / "logo.png"


def _content_bbox(img: Image.Image, threshold: int = 10) -> tuple[int, int, int, int]:
    if np is not None:
        arr = np.array(img)
        alpha = arr[:, :, 3]
        ys, xs = np.where(alpha > threshold)
        if len(xs) == 0:
            raise ValueError("logo has no opaque pixels")
        return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1

    # Pillow-only fallback
    alpha = img.split()[-1]
    return alpha.getbbox() or (0, 0, img.width, img.height)


def _wordmark_gap_row(img: Image.Image) -> int:
    """Return the first row of the gap between emblem and wordmark."""
    if np is None:
        # Without numpy, keep the full trimmed image as the emblem source.
        return img.height

    arr = np.array(img)
    density = (arr[:, :, 3] > 20).sum(axis=1)
    h = len(density)
    gaps: list[tuple[int, int, int]] = []
    in_gap = False
    start = 0
    for i, d in enumerate(density):
        if d < 30:
            if not in_gap:
                in_gap, start = True, i
        elif in_gap:
            gaps.append((start, i - 1, i - start))
            in_gap = False
    for start, _end, width in gaps:
        if width > 5 and start > h * 0.4:
            return start
    return img.height


def fit_square(img: Image.Image, size: int) -> Image.Image:
    w, h = img.size
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


def fit_shortest_side(img: Image.Image, short_side: int) -> Image.Image:
    w, h = img.size
    if w <= h:
        nw, nh = short_side, max(1, round(h * short_side / w))
    else:
        nh, nw = short_side, max(1, round(w * short_side / h))
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def generate_brand_images(source: Path) -> dict[str, Image.Image]:
    im = Image.open(source).convert("RGBA")
    left, top, right, bottom = _content_bbox(im)
    trimmed = im.crop((left, top, right, bottom))

    gap = _wordmark_gap_row(trimmed)
    emblem = trimmed.crop((0, 0, trimmed.width, gap))
    el, et, er, eb = _content_bbox(emblem)
    emblem = emblem.crop((el, et, er, eb))

    return {
        "icon.png": fit_square(emblem, 256),
        "icon@2x.png": fit_square(emblem, 512),
        "logo.png": fit_shortest_side(trimmed, 256),
        "logo@2x.png": fit_shortest_side(trimmed, 512),
        "readme_logo.png": fit_shortest_side(trimmed, 320),
    }


def sync(
    source: Path,
    brand_dir: Path = DEFAULT_OUT_BRAND,
    readme_logo: Path = DEFAULT_OUT_README,
) -> list[Path]:
    images = generate_brand_images(source)
    brand_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name in ("icon.png", "icon@2x.png", "logo.png", "logo@2x.png"):
        path = brand_dir / name
        images[name].save(path, optimize=True)
        written.append(path)
    readme_logo.parent.mkdir(parents=True, exist_ok=True)
    images["readme_logo.png"].save(readme_logo, optimize=True)
    written.append(readme_logo)
    return written


def _default_source() -> Path:
    if MONOREPO_KIT.is_file():
        return MONOREPO_KIT
    raise SystemExit(
        "Could not find brand_kit/logo.png. Pass --source explicitly.\n"
        f"Looked at: {MONOREPO_KIT}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Path to brand_kit/logo.png (default: monorepo brand_kit)",
    )
    args = parser.parse_args(argv)
    source = args.source or _default_source()
    if not source.is_file():
        raise SystemExit(f"Source logo not found: {source}")
    written = sync(source)
    for path in written:
        print(f"wrote {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
