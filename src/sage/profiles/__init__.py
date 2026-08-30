from .png_exp import PngExperimentalProfile

__all__ = ["PngExperimentalProfile"]
"""SAGE media transport profiles."""

from .jpeg import JpegMetadataProfile
from .png_exp import PngExperimentalProfile
from .webp import WebpMetadataProfile


def profile_for_format(format_name: str):
    name = format_name.upper()
    if name == "PNG":
        return PngExperimentalProfile()
    if name in {"JPEG", "JPG"}:
        return JpegMetadataProfile()
    if name == "WEBP":
        return WebpMetadataProfile()
    raise ValueError(f"Unsupported SAGE image format: {format_name}")


__all__ = ["JpegMetadataProfile", "PngExperimentalProfile", "WebpMetadataProfile", "profile_for_format"]
