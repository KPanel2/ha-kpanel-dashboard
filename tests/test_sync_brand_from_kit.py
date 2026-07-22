"""Tests for brand_kit → HA brand/ sync helper."""

from pathlib import Path

from PIL import Image

from scripts.sync_brand_from_kit import generate_brand_images, sync

REPO = Path(__file__).resolve().parents[1]
KIT = REPO.parents[1] / "brand_kit" / "logo.png"


def test_generate_brand_images_sizes(tmp_path: Path) -> None:
    if not KIT.is_file():
        # Standalone clone of the submodule without the monorepo kit.
        src = tmp_path / "logo.png"
        Image.new("RGBA", (400, 380), (0, 0, 0, 0)).save(src)
        # Draw emblem + gap + wordmark so gap detection has content.
        img = Image.new("RGBA", (400, 380), (0, 0, 0, 0))
        for y in range(40, 220):
            for x in range(80, 320):
                img.putpixel((x, y), (34, 199, 255, 255))
        for y in range(280, 340):
            for x in range(100, 300):
                img.putpixel((x, y), (139, 231, 30, 255))
        img.save(src)
    else:
        src = KIT

    images = generate_brand_images(src)
    assert images["icon.png"].size == (256, 256)
    assert images["icon@2x.png"].size == (512, 512)
    assert min(images["logo.png"].size) == 256
    assert min(images["logo@2x.png"].size) == 512


def test_sync_writes_brand_and_readme(tmp_path: Path) -> None:
    src = tmp_path / "logo.png"
    img = Image.new("RGBA", (200, 180), (0, 0, 0, 0))
    for y in range(10, 100):
        for x in range(20, 180):
            img.putpixel((x, y), (34, 199, 255, 255))
    for y in range(130, 170):
        for x in range(40, 160):
            img.putpixel((x, y), (139, 231, 30, 255))
    img.save(src)

    brand_dir = tmp_path / "brand"
    readme = tmp_path / "images" / "logo.png"
    written = sync(src, brand_dir=brand_dir, readme_logo=readme)

    assert (brand_dir / "icon.png").is_file()
    assert (brand_dir / "icon@2x.png").is_file()
    assert (brand_dir / "logo.png").is_file()
    assert (brand_dir / "logo@2x.png").is_file()
    assert readme.is_file()
    assert len(written) == 5
