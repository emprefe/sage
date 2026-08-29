"""Run graded image transforms against a locally generated marked image."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from sage.decode import decode


def variants(image: Image.Image):
    for radius in (0.5, 1, 2, 3):
        yield f"blur_{radius}", image.filter(ImageFilter.GaussianBlur(radius))
    for factor in (0.8, 0.9, 1.1, 1.3):
        yield f"brightness_{str(factor).replace('.', '_')}", ImageEnhance.Brightness(image).enhance(factor)
    for factor in (0.7, 0.85, 1.15, 1.3):
        yield f"contrast_{str(factor).replace('.', '_')}", ImageEnhance.Contrast(image).enhance(factor)
    for color, label in (((255, 255, 255), "white"), ((20, 20, 20), "dark")):
        for border in (5, 10, 25, 50):
            yield f"{label}_border_{border}", ImageOps.expand(image, border=border, fill=color)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(args.input) as source:
        image = source.convert("RGB")
    rows = []
    for name, derivative in variants(image):
        path = args.output_dir / f"{name}.png"
        derivative.save(path, format="PNG", optimize=False, compress_level=9)
        result = decode(path.read_bytes(), "STRICT")
        rows.append({
            "name": name,
            "size": derivative.size,
            "metadata": result.metadata_evidence[0].status if result.metadata_evidence else None,
            "concealed": result.concealed_evidence[0].status if result.concealed_evidence else None,
            "presence": result.presence,
            "record_recovered": result.record is not None,
        })
    report = {"input": str(args.input), "count": len(rows), "results": rows}
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
