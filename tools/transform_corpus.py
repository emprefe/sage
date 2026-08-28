"""Generate deterministic SAGE transformation derivatives and recovery reports."""

from __future__ import annotations

import argparse
import io
import json
import math
import time
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from sage.decode import decode


def _png_roundtrip(image: Image.Image) -> Image.Image:
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=False, compress_level=9)
    stream.seek(0)
    return Image.open(stream).convert("RGBA").copy()


def _psnr(left: Image.Image, right: Image.Image) -> float | None:
    if left.size != right.size:
        return None
    a = list(left.convert("RGB").get_flattened_data())
    b = list(right.convert("RGB").get_flattened_data())
    mse = sum((x - y) ** 2 for px, py in zip(a, b) for x, y in zip(px, py)) / (len(a) * 3)
    return None if mse == 0 else round(10 * math.log10((255 * 255) / mse), 4)


def _derivatives(image: Image.Image):
    yield "png_roundtrip", _png_roundtrip(image), {"format": "PNG"}, ".png"
    for quality in (95, 85, 70, 50):
        stream = io.BytesIO()
        image.convert("RGB").save(stream, format="JPEG", quality=quality, optimize=False)
        stream.seek(0)
        lossy = Image.open(stream).convert("RGB").copy()
        yield f"jpeg_q{quality}", lossy, {"format": "JPEG", "quality": quality}, ".jpg"
        yield f"jpeg_q{quality}_rasterized_png", lossy, {"format": "PNG", "source_format": "JPEG", "quality": quality}, ".png"
    webp = io.BytesIO()
    image.convert("RGB").save(webp, format="WEBP", quality=80, method=4)
    webp.seek(0)
    lossy_webp = Image.open(webp).convert("RGB").copy()
    yield "webp_q80", lossy_webp, {"format": "WEBP", "quality": 80}, ".webp"
    yield "webp_q80_rasterized_png", lossy_webp, {"format": "PNG", "source_format": "WEBP", "quality": 80}, ".png"
    for percent in (75, 50, 25):
        size = (max(1, image.width * percent // 100), max(1, image.height * percent // 100))
        yield f"resize_{percent}", image.resize(size, Image.Resampling.LANCZOS), {"percent": percent}, ".png"
    for percent in (90, 75, 50, 25):
        width = max(1, image.width * percent // 100)
        height = max(1, image.height * percent // 100)
        left, top = (image.width - width) // 2, (image.height - height) // 2
        yield f"crop_{percent}", image.crop((left, top, left + width, top + height)), {"retained_percent": percent}, ".png"
    yield "blur", image.filter(ImageFilter.GaussianBlur(radius=1.0)), {"radius": 1.0}, ".png"
    yield "sharpen", image.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3)), {"radius": 1, "percent": 150}, ".png"
    yield "brightness_110", ImageEnhance.Brightness(image).enhance(1.10), {"factor": 1.10}, ".png"
    yield "contrast_110", ImageEnhance.Contrast(image).enhance(1.10), {"factor": 1.10}, ".png"
    yield "border_10", ImageOps.expand(image, border=10, fill=(255, 255, 255, 255)), {"border": 10}, ".png"
    yield "rotate_5", image.rotate(5, resample=Image.Resampling.BICUBIC, expand=False), {"degrees": 5}, ".png"
    screenshot = image.resize((image.width * 2, image.height * 2), Image.Resampling.BILINEAR)
    screenshot = screenshot.resize(image.size, Image.Resampling.BILINEAR)
    yield "screenshot_like_raster", screenshot, {"upscale": 2, "downscale": 0.5}, ".png"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    baseline_bytes = args.input.read_bytes()
    with Image.open(io.BytesIO(baseline_bytes)) as opened:
        baseline = opened.convert("RGBA").copy()
    baseline_result = decode(baseline_bytes, "STRICT")
    baseline_record = baseline_result.record
    rows = []
    for name, derivative, parameters, suffix in _derivatives(baseline):
        path = args.output_dir / f"{name}{suffix}"
        if suffix == ".png":
            derivative.save(path, format="PNG", optimize=False, compress_level=9)
        elif suffix == ".jpg":
            derivative.save(path, format="JPEG", quality=parameters["quality"], optimize=False)
        else:
            derivative.save(path, format="WEBP", quality=parameters["quality"], method=4)
        data = path.read_bytes()
        started = time.perf_counter()
        result = decode(data, "STRICT")
        metadata = result.metadata_evidence[0] if result.metadata_evidence else None
        concealed = result.concealed_evidence[0] if result.concealed_evidence else None
        rows.append({
            "name": name,
            "parameters": parameters,
            "format": parameters.get("format", "PNG"),
            "profile_transport_supported": parameters.get("format", "PNG") == "PNG",
            "output": str(path),
            "output_bytes": len(data),
            "psnr_db": _psnr(baseline, derivative),
            "metadata_status": metadata.status if metadata else None,
            "concealed_status": concealed.status if concealed else None,
            "presence": result.presence,
            "record_equal_to_baseline": result.record is not None and baseline_record is not None and result.record == baseline_record,
            "recovery_quality": result.recovery_quality,
            "recovery_metrics": result.recovery_metrics,
            "decode_runtime_ms": round((time.perf_counter() - started) * 1000, 3),
        })
    report = {
        "tool": "sage_transform_corpus",
        "version": "0.01",
        "baseline": str(args.input),
        "baseline_presence": baseline_result.presence,
        "baseline_record_recovered": baseline_record is not None,
        "derivatives": rows,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
